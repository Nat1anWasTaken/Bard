class Option:
    """
    A class representing a choice option.
    """
    def __init__(self, choice_id: str, content: str):
        """
        A class representing a choice option.
        :param choice_id: The choice ID.
        :param content: The content of the choice.
        """
        self.choice_id: str = choice_id
        self.content: str = content

    @classmethod
    def from_dict(cls, data: dict) -> "Option":
        """
        Create an Option instance from a dict.
        :param data: The dict to create the Option instance from.
        :return: The Option instance.
        """
        return cls(
            choice_id=data["id"],
            content=data["content"]
        )


class Response:
    """
    A class representing a response from Google Bard.
    """
    def __init__(self,
                 content: str, conversation_id: str, response_id: str,
                 factuality_queries: list, text_query: list[str], choices: list[Option]):
        self.content: str = content
        self.conversation_id: str = conversation_id
        self.response_id: str = response_id
        self.factuality_queries: list = factuality_queries
        self.text_query: list[str] = text_query
        self.choices: list[Option] = choices

    @classmethod
    def from_dict(cls, data: dict) -> "Response":
        return cls(
            content=data["content"],
            conversation_id=data["conversation_id"],
            response_id=data["response_id"],
            factuality_queries=data["factuality_queries"],
            text_query=data["text_query"],
            choices=[Option.from_dict(choice) for choice in data["choices"]]
        )
