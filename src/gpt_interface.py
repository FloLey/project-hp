from config import PROMPT, client


class GPTInterface:
    @staticmethod
    def get_gpt_response(input_text, conversation_history):
        conversation_history.append({"role": "user", "content": input_text})
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PROMPT},
                *conversation_history
            ]
        )
        gpt_response = response.choices[0].message.content
        conversation_history.append(
            {"role": "assistant", "content": gpt_response})
        return gpt_response
