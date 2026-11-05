import os
import time
import json
import math
import requests

from pathlib import Path
from dotenv import load_dotenv


# --------------------------------------------------
# GROQ API CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE, override=True)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

MODEL_NAME = "openai/gpt-oss-120b"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

print("ENV FILE EXISTS:", ENV_FILE.exists())
print("GROQ API KEY LOADED:", bool(GROQ_API_KEY))
print("GROQ MODEL:", MODEL_NAME)


# --------------------------------------------------
# COMMON GROQ FUNCTION
# --------------------------------------------------

def call_groq(prompt, timeout=180):

    api_key = (
        os.getenv("GROQ_API_KEY", "").strip()
        or GROQ_API_KEY
    )

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing. "
            "Configure it in your .env file or Render environment variables."
        )

    start_time = time.time()

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert interview evaluator. "
                    "Evaluate answers fairly and objectively. "
                    "Return only valid JSON matching the requested structure. "
                    "Do not include Markdown or additional commentary."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,
        "max_completion_tokens": 8000,
        "reasoning_effort": "low",
        "stream": False,
        "response_format": {
            "type": "json_object"
        }
    }

    try:

        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=timeout
        )

        response.raise_for_status()

        result = response.json()

        choices = result.get("choices", [])

        if not choices:
            raise ValueError("Groq returned no response choices.")

        message = choices[0].get("message", {})
        ai_text = message.get("content")

        if not isinstance(ai_text, str) or not ai_text.strip():
            raise ValueError(
                "Groq returned empty content. "
                "Check completion token limits and model response."
            )

        ai_text = ai_text.strip()

        # Remove accidental Markdown code fences
        if ai_text.startswith("```"):
            ai_text = ai_text.replace("```json", "", 1)

            if ai_text.endswith("```"):
                ai_text = ai_text[:-3]

            ai_text = ai_text.strip()

        evaluation = json.loads(ai_text)

        if not isinstance(evaluation, dict):
            raise ValueError("Groq returned an invalid JSON object.")

        print(
            "GROQ RESPONSE TIME:",
            round(time.time() - start_time, 2),
            "seconds"
        )

        return evaluation

    except requests.exceptions.Timeout as error:

        raise RuntimeError(
            "Groq API request timed out. Please try again."
        ) from error

    except requests.exceptions.HTTPError as error:

        status_code = (
            error.response.status_code
            if error.response is not None
            else "Unknown"
        )

        response_text = (
            error.response.text[:500]
            if error.response is not None
            else str(error)
        )

        if status_code == 429:
            message = (
                "Groq API rate limit reached. Please wait and try again."
            )

        elif status_code in (401, 403):
            message = (
                "Groq API authentication or permission failed. "
                "Check your API key and account access."
            )

        elif status_code == 404:
            message = (
                f"Groq model not found or unavailable: {MODEL_NAME}"
            )

        elif status_code == 400:
            message = (
                f"Groq rejected the request: {response_text}"
            )

        else:
            message = (
                f"Groq API request failed with status "
                f"{status_code}: {response_text}"
            )

        raise RuntimeError(message) from error

    except requests.exceptions.RequestException as error:

        raise RuntimeError(
            f"Groq network request failed: {error}"
        ) from error

    except (ValueError, KeyError, IndexError) as error:

        raise RuntimeError(
            f"Groq evaluation response error: {error}"
        ) from error


# --------------------------------------------------
# SCORE VALIDATION
# --------------------------------------------------

def safe_score(value):

    try:

        score = float(value)

        if not math.isfinite(score):
            raise ValueError("Score must be a finite number.")

        if not 0 <= score <= 100:
            raise ValueError("Score must be between 0 and 100.")

        return round(score, 1)

    except (ValueError, TypeError):

        raise ValueError(
            f"Invalid evaluation score: {value!r}"
        )


# --------------------------------------------------
# ANSWER QUALITY VALIDATION
# --------------------------------------------------

def is_insufficient_answer(answer):

    answer = (answer or "").strip()

    if not answer:
        return True

    meaningful_text = "".join(
        character
        for character in answer
        if character.isalnum()
    )

    if len(meaningful_text) < 3:
        return True

    if len(set(meaningful_text.lower())) == 1:
        return True

    return False


# --------------------------------------------------
# INSUFFICIENT ANSWER RESULT
# --------------------------------------------------

def insufficient_answer_result():

    return {
        "score": 0,
        "relevance": 0,
        "technical_accuracy": 0,
        "completeness": 0,
        "communication": 0,
        "strengths": "No meaningful answer was provided.",
        "weaknesses": (
            "The response is too short or does not contain "
            "enough information to evaluate."
        ),
        "suggestions": (
            "Provide a relevant explanation using complete "
            "sentences and supporting details."
        ),
        "evaluation_status": "success"
    }


# --------------------------------------------------
# DEFAULT EVALUATION RESULT
# --------------------------------------------------

def default_result(message):

    return {
        "score": None,
        "relevance": None,
        "technical_accuracy": None,
        "completeness": None,
        "communication": None,
        "strengths": "AI evaluation could not be completed.",
        "weaknesses": f"Evaluation error: {message}",
        "suggestions": (
            "Please check the AI evaluator configuration and try again."
        ),
        "evaluation_status": "failed"
    }


# --------------------------------------------------
# FORMAT AI EVALUATION
# --------------------------------------------------

def format_evaluation(evaluation):

    if not isinstance(evaluation, dict):
        raise ValueError("Invalid evaluation response.")

    required_fields = [
        "relevance",
        "technical_accuracy",
        "completeness",
        "communication"
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in evaluation
    ]

    if missing_fields:
        raise ValueError(
            "AI response is missing score fields: "
            + ", ".join(missing_fields)
        )

    relevance = safe_score(evaluation["relevance"])

    technical_accuracy = safe_score(
        evaluation["technical_accuracy"]
    )

    completeness = safe_score(
        evaluation["completeness"]
    )

    communication = safe_score(
        evaluation["communication"]
    )

    overall_score = round(
        (
            relevance
            + technical_accuracy
            + completeness
            + communication
        ) / 4,
        1
    )

    return {
        "score": overall_score,
        "relevance": relevance,
        "technical_accuracy": technical_accuracy,
        "completeness": completeness,
        "communication": communication,
        "strengths": str(
            evaluation.get("strengths") or "No strengths identified."
        ),
        "weaknesses": str(
            evaluation.get("weaknesses") or "No weaknesses identified."
        ),
        "suggestions": str(
            evaluation.get("suggestions")
            or "Continue practising your answers."
        ),
        "evaluation_status": "success"
    }


# --------------------------------------------------
# SINGLE ANSWER EVALUATION
# --------------------------------------------------

def evaluate_with_gpt(question, answer, role="Software Engineer"):

    answer = (answer or "").strip()
    question = (question or "").strip()

    if is_insufficient_answer(answer):
        return insufficient_answer_result()

    prompt = f"""
You are an expert technical and HR interview evaluator.

Evaluate the candidate's answer fairly and objectively.

JOB ROLE:
{role}

INTERVIEW QUESTION:
{question}

CANDIDATE ANSWER:
{answer}

EVALUATION CRITERIA:

1. RELEVANCE:
Evaluate how directly the answer addresses the question.

2. TECHNICAL ACCURACY:
Evaluate whether the concepts, facts and explanations are correct.
For HR questions, evaluate the appropriateness of the response.

3. COMPLETENESS:
Evaluate whether the answer covers the important points.

4. COMMUNICATION:
Evaluate clarity, logical structure and explanation quality.

SCORING RULES:

- Give each criterion a score from 0 to 100.
- A correct and relevant answer should receive high marks.
- Do not give zero to a correct answer.
- Give zero only when the answer is completely irrelevant
  or contains no correct information.
- Give proportionate marks for partially correct answers.
- Do not reward answer length alone.
- Do not expect technical content for non-technical HR questions.
- Evaluate according to the selected job role.
- Do not invent information that the candidate did not provide.
- Calculate the overall score as the average of the four criteria.

FEEDBACK:

- Strengths: Mention what the candidate did well.
- Weaknesses: Mention what needs improvement.
- Suggestions: Give practical ways to improve the answer.
- Keep feedback specific and constructive.

Return ONLY valid JSON using this structure:

{{
    "score": 75,
    "relevance": 80,
    "technical_accuracy": 70,
    "completeness": 75,
    "communication": 75,
    "strengths": "The answer explains the main concept clearly.",
    "weaknesses": "Some important details are missing.",
    "suggestions": "Add a practical example to support the explanation."
}}
"""

    try:

        evaluation = call_groq(prompt)

        return format_evaluation(evaluation)

    except Exception as error:

        print("SINGLE ANSWER AI ERROR:", repr(error))

        return default_result(error)


# --------------------------------------------------
# BATCH INTERVIEW EVALUATION
# --------------------------------------------------

def evaluate_interview(questions, answers, role="Software Engineer"):

    if not isinstance(questions, list) or not questions:
        return []

    if not isinstance(answers, list):
        answers = []

    prepared_answers = []

    for index in range(len(questions)):

        answer = (
            answers[index]
            if index < len(answers)
            else ""
        )

        if isinstance(answer, str):
            prepared_answers.append(answer.strip())
        else:
            prepared_answers.append("")

    results = [None] * len(questions)

    prompt_data = []
    original_indexes = []

    for index, answer in enumerate(prepared_answers):

        if is_insufficient_answer(answer):

            results[index] = insufficient_answer_result()

        else:

            prompt_data.append({
                "question": str(questions[index]),
                "answer": answer
            })

            original_indexes.append(index)

    if not prompt_data:
        return results

    prompt = f"""
You are an expert technical and HR interview evaluator.

JOB ROLE:
{role}

Evaluate every candidate answer independently.

QUESTIONS AND ANSWERS:
{json.dumps(prompt_data, ensure_ascii=False)}

Evaluate each answer using these four criteria:

1. Relevance:
How directly does the answer address the question?

2. Technical Accuracy:
Are the concepts, facts and explanations correct?
For HR questions, evaluate the appropriateness of the response.

3. Completeness:
Does the answer cover the important points?

4. Communication:
Is the answer clear, logical and well structured?

SCORING RULES:

- Give each criterion a score from 0 to 100.
- A correct and relevant answer should receive high marks.
- Do not give zero to a correct answer.
- Give zero only when an answer is completely irrelevant
  or contains no correct information.
- Give proportionate marks for partially correct answers.
- Evaluate every answer independently.
- Do not reward irrelevant or incorrect answers.
- Do not reward length alone.
- Consider the selected job role.
- Do not expect technical explanations for non-technical questions.
- Calculate the overall score as the average of the four criteria.

FEEDBACK RULES:

- Give specific strengths.
- Identify actual weaknesses.
- Provide practical suggestions.
- Keep each feedback field concise.
- Do not use Markdown.

Return ONLY valid JSON in this exact structure:

{{
    "results": [
        {{
            "score": 75,
            "relevance": 80,
            "technical_accuracy": 70,
            "completeness": 75,
            "communication": 75,
            "strengths": "The main concept is explained clearly.",
            "weaknesses": "Some important details are missing.",
            "suggestions": "Include a relevant practical example."
        }}
    ]
}}

IMPORTANT:

- Return exactly {len(prompt_data)} results.
- Preserve the original order.
- Do not combine answers.
- Do not skip any submitted answer.
- Return valid JSON only.
"""

    try:

        evaluation = call_groq(prompt, timeout=180)

        ai_results = evaluation.get("results", [])

        if not isinstance(ai_results, list):
            raise ValueError("Invalid AI results format.")

        if len(ai_results) != len(original_indexes):
            raise ValueError(
                "Groq returned an unexpected number of evaluation results."
            )

        for position, original_index in enumerate(original_indexes):

            results[original_index] = format_evaluation(
                ai_results[position]
            )

        return results

    except Exception as error:

        print("BATCH INTERVIEW AI ERROR:", repr(error))

        for original_index in original_indexes:
            results[original_index] = default_result(error)

        return results
