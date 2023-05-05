import json
import logging
import random
import re
import string
from asyncio import get_event_loop, AbstractEventLoop
from typing import Union

from aiohttp import ClientSession, ClientResponse

from bard.error import BardError, NoLastResponseError
from bard.response import Response, Option
from bard.utils import MISSING, get


class Bard:
    """
    A class to interact with Google Bard.
    """

    def __init__(self):
        self._reqid: int = int("".join(random.choices(string.digits, k=4)))
        self.conversation_id: str = ""
        self.response_id: str = ""
        self.choice_id: str = ""

        self.last_response: Response = MISSING

        self.session: ClientSession = MISSING
        self.SNlM0e: str = MISSING

        self.logger: logging.Logger = logging.getLogger("bard")

    async def initialize(self, session_id: str, loop: AbstractEventLoop = None) -> "Chatbot":
        """
        Initialize the Google Bard session. This must be called before using the ask method.
        :param session_id: The 1PSID cookie from Google.
        :param loop: The event loop to use.
        :return: The Chatbot instance.
        """
        self.logger.info("Initializing session...")
        self.session = ClientSession(
            loop=loop or get_event_loop(),
            headers={
                "Host": "bard.google.com",
                "X-Same-Domain": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "Origin": "https://bard.google.com",
                "Referer": "https://bard.google.com/",
            },
            cookies={"__Secure-1PSID": session_id}
        )

        self.logger.info("Getting SNlM0e...")
        self.SNlM0e: str = await self.__get_snlm0e(self.session)

        return self

    @staticmethod
    async def __get_snlm0e(session: ClientSession) -> str:
        """
        Get the SNlM0e value from Google Bard.
        :param session: The aiohttp session to use.
        :return: The SNlM0e value.
        """
        response: ClientResponse = await session.get(url="https://bard.google.com/", timeout=10)

        if response.status != 200:
            raise Exception("Could not get Google Bard")

        response_text: str = await response.text()

        try:
            SNlM0e = re.search(r"SNlM0e\":\"(.*?)\"", response_text).group(1)
        except AttributeError:
            raise ValueError("Could not get SNlM0e, is the session ID correct?")

        return SNlM0e

    async def ask(self, message: str) -> Response:
        """
        Send a message to Google Bard and return the response.
        :param message: The message to send to Google Bard.
        :return: A dict containing the response from Google Bard.
        """
        self.logger.info("Asking %s...", message)
        # url params
        params: dict = {
            "bl": "boq_assistant-bard-web-server_20230419.00_p1",
            "_reqid": str(self._reqid),
            "rt": "c",
        }

        # message arr -> data["f.req"]. Message is double json stringified
        message_struct: list = [
            [message],
            None,
            [self.conversation_id, self.response_id, self.choice_id],
        ]
        data: dict = {
            "f.req": json.dumps([None, json.dumps(message_struct)]),
            "at": self.SNlM0e,
        }

        # do the request!
        response: ClientResponse = await self.session.post(
            "https://bard.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate",
            params=params,
            data=data,
            timeout=120,
        )

        response_content: str = await response.text()
        self.logger.info("Got the response %s", response_content)

        chat_data = json.loads(response_content.splitlines()[3])[0][2]

        if not chat_data:
            raise BardError(f"Could not get response from Google Bard. {response_content}")

        json_chat_data = json.loads(chat_data)

        self.last_response = Response(
            content=json_chat_data[0][0],
            conversation_id=json_chat_data[1][0],
            response_id=json_chat_data[1][1],
            factuality_queries=json_chat_data[3],
            text_query=json_chat_data[2][0] if json_chat_data[2] is not None else "",
            choices=[Option(choice_id=i[0], content=i[1][0]) for i in json_chat_data[4]]
        )

        self.conversation_id = self.last_response.conversation_id
        self.response_id = self.last_response.response_id
        self.choice_id = self.last_response.choices[0].choice_id
        self._reqid += 100000

        return self.last_response

    def choose(self, choice_id: str) -> Union[Option, None]:
        """
        Choose a response from the conversation.
        :param choice_id: The conversation to choose from.
        :return: The chosen response. None if the response does not exist.
        """
        if not self.last_response:
            raise NoLastResponseError("No last response to choose from.")

        self.logger.info("Selecting response %s...", choice_id)

        result: Option = get(self.last_response.choices, choice_id=choice_id)

        if not result:
            return None

        # Swap the chosen response to the first position
        self.last_response.choices.append(
            Option(
                choice_id=self.last_response.response_id,
                content=self.last_response.content
            )
        )  # Add the current response to the end of the list

        self.last_response.choices.remove(result)

        self.last_response.response_id = result.choice_id
        self.last_response.content = result.content

        self.choice_id = self.last_response.choices[0].choice_id
        self.response_id = result.choice_id

        return result

    def reset(self):
        """
        Reset the conversation.
        :return: Nothing
        """
        self.logger.info("Resetting conversation...")

        self.conversation_id = ""
        self.response_id = ""
        self.choice_id = ""
        self._reqid = int("".join(random.choices(string.digits, k=4)))
