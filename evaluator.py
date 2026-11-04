import re
from ai_modules.answer_evaluator import evaluate_with_gpt


def evaluate_answer(question, answer, role="Software Engineer"):
    """
    Evaluates one interview answer using the local Ollama AI model.
    """

    answer = (answer or "").strip()
    question = (question or "").strip()

    words = re.findall(r"\b[\w+#.-]+\b", answer)
    word_count = len(words)

    if not answer:
        return {
            "score": 0,
            "word_count": 0,
            "relevance": 0,
            "technical_accuracy": 0,
            "completeness": 0,
            "communication": 0,
            "feedback": "No answer provided. Please try answering the question.",
            "strengths": "No answer was provided.",
            "weaknesses": "The question was not answered.",
            "suggestions": "Provide a clear answer with an explanation and example."
        }

    try:
        evaluation = evaluate_with_gpt(
            question=question,
            answer=answer,
            role=role
        )

        if not isinstance(evaluation, dict):
            raise ValueError("Invalid evaluation response.")

    except Exception as error:
        print("ANSWER EVALUATION ERROR:", error)

        return {
            "score": 0,
            "word_count": word_count,
            "relevance": 0,
            "technical_accuracy": 0,
            "completeness": 0,
            "communication": 0,
            "feedback": "AI evaluation is temporarily unavailable.",
            "strengths": "Evaluation could not be completed.",
            "weaknesses": str(error),
            "suggestions": "Check whether Ollama is running and try again."
        }

    def safe_score(value):
        try:
            score = float(value)

            if not (score == score and abs(score) != float("inf")):
                return 0

            return round(max(0, min(100, score)), 1)

        except (ValueError, TypeError):
            return 0

    score = safe_score(evaluation.get("score", 0))
    relevance = safe_score(evaluation.get("relevance", 0))

    technical_accuracy = safe_score(
        evaluation.get("technical_accuracy", 0)
    )

    completeness = safe_score(
        evaluation.get("completeness", 0)
    )

    communication = safe_score(
        evaluation.get("communication", 0)
    )

    strengths = str(
        evaluation.get("strengths", "No strengths identified.")
    )

    weaknesses = str(
        evaluation.get("weaknesses", "No weaknesses identified.")
    )

    suggestions = str(
        evaluation.get("suggestions", "Continue practising.")
    )

    feedback = (
        f"Overall Score: {score}/100\n\n"
        f"Relevance: {relevance}/100\n"
        f"Technical Accuracy: {technical_accuracy}/100\n"
        f"Completeness: {completeness}/100\n"
        f"Communication: {communication}/100\n\n"
        f"Strengths:\n{strengths}\n\n"
        f"Weaknesses:\n{weaknesses}\n\n"
        f"Suggestions:\n{suggestions}"
    )

    return {
        "score": score,
        "word_count": word_count,
        "relevance": relevance,
        "technical_accuracy": technical_accuracy,
        "completeness": completeness,
        "communication": communication,
        "feedback": feedback,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions
    }
