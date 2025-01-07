from openai import OpenAI
import time
import json
import textstat
from typing import Dict


class EssayGrader:
    def __init__(
        self,
        task_type: str,
        student_essay: str,
        student_year_level: int,
        openai_config: Dict[str, str],
        prompts_config: Dict[str, str],
    ):
        self.task_type = task_type
        self.student_essay = student_essay
        self.student_year_level = student_year_level
        self.student_expected_flesch = {
            2: 100,
            3: 96,
            4: 94,
            5: 90,
            6: 85,
            7: 75,
            8: 65,
            9: 65,
            10: 60,
        }[self.student_year_level]
        self.openai_client: OpenAI = OpenAI(api_key=openai_config["openai_api_key"])
        self.marking_model: str = openai_config["openai_marking_model"]
        self.feedback_model: str = openai_config["openai_feedback_model"]
        self.marking_prompt: str = prompts_config[f"marking_{task_type}"]
        self.feedback_prompt: str = prompts_config[f"feedback_{task_type}"]

    def get_openai_score(self) -> None:
        score_time = time.time()
        resp = self.openai_client.chat.completions.create(
            model=self.marking_model,
            messages=[
                {"role": "system", "content": self.marking_prompt},
                {"role": "user", "content": self.student_essay},
            ],
            max_completion_tokens=3000,
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        self.marks: Dict[str, int] = json.loads(resp.choices[0].message.content)
        self.score_time: float = round(time.time() - score_time, 1)

    def get_openai_feedback(self) -> None:
        feedback_time = time.time()
        resp = self.openai_client.chat.completions.create(
            model=self.feedback_model,
            messages=[
                {"role": "system", "content": self.feedback_prompt},
                {"role": "user", "content": json.dumps(self.marks)},
                {"role": "user", "content": self.student_essay},
            ],
            max_completion_tokens=4000,
            response_format={"type": "json_object"},
        )

        self.feedback: Dict[str, Dict[str, str]] = json.loads(
            resp.choices[0].message.content
        )
        self.feedback_time: float = round(time.time() - feedback_time, 1)
        self.get_feedback_flesch()

    def get_feedback_flesch(self) -> None:
        combined_to_string = []
        for _, details in self.feedback.items():
            combined_to_string.append(details["feedback"])
            combined_to_string.append(details["progression"])
        self.feedback_flesch: int = int(
            textstat.flesch_reading_ease(" ".join(combined_to_string))
        )
