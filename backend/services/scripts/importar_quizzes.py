
import json
import subprocess
import sys
from pathlib import Path

# Permite importar os módulos do projeto.
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from backend.database.connection import SessionLocal
from backend.database.models import Quiz, PerguntaQuiz


CODIGOS = [
    "quiz-dia",
    "brasileirao",
    "laliga",
    "champions",
    "copa-brasil",
    "copa-mundo",
    "selecao-brasil",
]

# Lê o arquivo JavaScript sem precisar publicá-lo no backend.
NODE_CODE = r"""
const fs = require("fs");
const vm = require("vm");

let source = fs.readFileSync(process.argv[1], "utf8");

source = source.replace(
    /export\s+const\s+quizzes\s*=/,
    "const quizzes ="
);

source += "\n;JSON.stringify(quizzes);";

const result = vm.runInNewContext(source);
process.stdout.write(result);
"""


def carregar_quizzes(caminho):
    resultado = subprocess.run(
        ["node", "-e", NODE_CODE, str(caminho)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(resultado.stdout)


def importar(caminho):
    quizzes = carregar_quizzes(caminho)

    if set(quizzes.keys()) != set(CODIGOS):
        raise ValueError("Os códigos dos quizzes não correspondem ao esperado.")

    total_geral = sum(
        len(quizzes[codigo]["perguntas"])
        for codigo in CODIGOS
    )

    if total_geral != 63:
        raise ValueError(
            f"Esperadas 63 perguntas, mas foram encontradas {total_geral}."
        )

    # Corrige somente a duplicação conhecida do enunciado.
    pergunta = quizzes["brasileirao"]["perguntas"][0]
    texto = pergunta["pergunta"]

    repeticao = (
        "Considerando os títulos brasileiros oficialmente reconhecidos "
        "pela CBF até o fim de 2025, qual clube é o maior campeão nacional?"
    )

    pergunta["pergunta"] = repeticao

    db = SessionLocal()

    try:
        for codigo in CODIGOS:
            quiz = (
                db.query(Quiz)
                .filter(Quiz.codigo == codigo)
                .one_or_none()
            )

            if quiz is None:
                raise ValueError(
                    f"Quiz '{codigo}' não encontrado no banco."
                )

            quantidade_existente = (
                db.query(PerguntaQuiz)
                .filter(PerguntaQuiz.quiz_id == quiz.id)
                .count()
            )

            if quantidade_existente > 0:
                raise ValueError(
                    f"O quiz '{codigo}' já possui perguntas. "
                    "Importação cancelada para evitar duplicações."
                )

            perguntas = quizzes[codigo]["perguntas"]

            for ordem, item in enumerate(perguntas, start=1):
                alternativas = item["alternativas"]
                resposta = item["respostaCorreta"]

                if len(alternativas) != 4:
                    raise ValueError(
                        f"Quiz '{codigo}', pergunta {ordem}: "
                        "esperadas quatro alternativas."
                    )

                if not isinstance(resposta, int) or not 0 <= resposta <= 3:
                    raise ValueError(
                        f"Quiz '{codigo}', pergunta {ordem}: "
                        "índice de resposta inválido."
                    )

                db.add(
                    PerguntaQuiz(
                        quiz_id=quiz.id,
                        enunciado=item["pergunta"],
                        alternativas=alternativas,
                        resposta_correta=resposta,
                        explicacao=item["explicacao"],
                        ordem=ordem,
                    )
                )

            quiz.total_perguntas = len(perguntas)

        db.commit()

        print("Importação concluída!")
        print(f"Total de perguntas cadastradas: {total_geral}")

        for codigo in CODIGOS:
            print(f"{codigo}: {len(quizzes[codigo]['perguntas'])} perguntas")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Uso: python backend/services/scripts/importar_quizzes.py "
            "CAMINHO_DO_ARQUIVO_quizPerguntas.js"
        )
        sys.exit(1)

    importar(Path(sys.argv[1]).resolve())
