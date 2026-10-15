"""Engineering understanding check for Campus Flow.

Question data, answer parsing, and scoring live here, completely
separate from the CLI menu loop in main.py. Input and output are
injected, so the quiz can be tested without a terminal.
"""

from dataclasses import dataclass, field
from pathlib import Path

VALID_ANSWERS = ("A", "B", "C", "D")

# 1-based question numbers whose answers the user must explain.
EXPLAIN_QUESTIONS = (3, 6)


@dataclass(frozen=True)
class Question:
    scenario: str
    prompt: str
    options: dict
    answer: str


QUESTIONS = [
    Question(
        scenario="Priority calculation",
        prompt=(
            "A ticket has high urgency and 12 affected users. "
            "What priority does Campus Flow assign?"
        ),
        options={
            "A": "low",
            "B": "high",
            "C": "critical",
            "D": "medium",
        },
        answer="C",
    ),
    Question(
        scenario="Priority from affected users",
        prompt=(
            "A ticket has LOW urgency but 10 affected users. "
            "What priority does it receive?"
        ),
        options={
            "A": "critical",
            "B": "high",
            "C": "medium",
            "D": "low",
        },
        answer="B",
    ),
    Question(
        scenario="Assignment before starting work",
        prompt=(
            "An open ticket has no assignee. A user tries to move it to "
            "in_progress. What happens?"
        ),
        options={
            "A": "It moves to in_progress and is auto-assigned.",
            "B": "It moves straight to resolved.",
            "C": "It stays open and nothing is reported.",
            "D": "It is rejected until the ticket is assigned.",
        },
        answer="D",
    ),
    Question(
        scenario="Workflow order",
        prompt=(
            "An open ticket (already assigned) is set directly to "
            "resolved. What happens?"
        ),
        options={
            "A": "It is rejected; it must be in_progress first.",
            "B": "It is resolved immediately.",
            "C": "It becomes in_progress automatically.",
            "D": "It is deleted from the system.",
        },
        answer="A",
    ),
    Question(
        scenario="Reopened tickets in reports",
        prompt=(
            "A resolved ticket is reopened. How do the report and the "
            "work queue treat it?"
        ),
        options={
            "A": "As resolved, and it stays out of the work queue.",
            "B": "As in_progress, and it stays out of the work queue.",
            "C": "As open, and it can appear in the work queue.",
            "D": "It is counted as both open and resolved.",
        },
        answer="C",
    ),
    Question(
        scenario="Combined search filters",
        prompt=(
            "A search supplies category=Network and status=open. "
            "Which tickets are returned?"
        ),
        options={
            "A": "Tickets matching either Network or open.",
            "B": "Only tickets that are both Network and open.",
            "C": "Only Network tickets; status is ignored.",
            "D": "All tickets, because filters are optional.",
        },
        answer="B",
    ),
]


@dataclass
class QuizResult:
    score: int
    total: int
    answers: list
    explanations: list = field(default_factory=list)


def parse_answer(raw):
    """Return 'A'-'D' for valid input (any case, padded), else None."""

    if not isinstance(raw, str):
        return None

    cleaned = raw.strip().upper()

    return cleaned if cleaned in VALID_ANSWERS else None


def score_answers(questions, answers):
    """Award one point per correct answer. Pure function, no I/O."""

    if len(questions) != len(answers):
        raise ValueError("Provide exactly one answer for each question.")

    score = 0

    for question, answer in zip(questions, answers):
        letter = parse_answer(answer)

        if letter is None:
            raise ValueError("Answers must be A, B, C, or D.")

        if letter == question.answer:
            score += 1

    return score


def _ask_answer(number, question, input_fn, output_fn):
    output_fn(f"\nQuestion {number}: {question.prompt}")

    for letter in VALID_ANSWERS:
        output_fn(f"  {letter}. {question.options[letter]}")

    while True:
        letter = parse_answer(input_fn("Your answer (A/B/C/D): "))

        if letter is not None:
            return letter

        output_fn("Invalid answer. Please enter A, B, C, or D.")


def _ask_explanation(number, question, input_fn, output_fn):
    while True:
        text = input_fn(
            f"Explain your answer to question {number} "
            f"({question.scenario}): "
        ).strip()

        if text:
            return text

        output_fn("An explanation is required. Please try again.")


def run_quiz(
    questions=None,
    input_fn=None,
    output_fn=None,
    explain_questions=EXPLAIN_QUESTIONS,
):
    """Run the quiz and return a QuizResult.

    input_fn and output_fn default to input/print, looked up at call
    time so tests can substitute their own.
    """

    questions = QUESTIONS if questions is None else questions
    input_fn = input if input_fn is None else input_fn
    output_fn = print if output_fn is None else output_fn
    answers = []
    explanations = []

    for number, question in enumerate(questions, start=1):
        letter = _ask_answer(number, question, input_fn, output_fn)
        answers.append(letter)

        if number in explain_questions:
            explanations.append(
                {
                    "question": number,
                    "scenario": question.scenario,
                    "answer": letter,
                    "explanation": _ask_explanation(
                        number, question, input_fn, output_fn
                    ),
                }
            )

    score = score_answers(questions, answers)
    output_fn(f"\nFinal score: {score}/{len(questions)}")

    for number, (question, letter) in enumerate(
        zip(questions, answers), start=1
    ):
        if letter != question.answer:
            output_fn(
                f"  Question {number}: you chose {letter}; "
                f"correct answer is {question.answer}."
            )

    return QuizResult(score, len(questions), answers, explanations)


def save_explanations(result, path="quiz_explanations.txt"):
    """Save explanations for mentor discussion."""

    lines = [f"Score: {result.score}/{result.total}", ""]

    for item in result.explanations:
        lines.append(
            f"Question {item['question']} ({item['scenario']}) "
            f"- answered {item['answer']}"
        )
        lines.append(item["explanation"])
        lines.append("")

    Path(path).write_text("\n".join(lines), encoding="utf-8")
    return Path(path)