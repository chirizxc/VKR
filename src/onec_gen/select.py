from collections.abc import Callable
from typing import Any

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.styles import Style
from questionary import utils
from questionary.constants import DEFAULT_QUESTION_PREFIX, DEFAULT_SELECTED_POINTER
from questionary.prompts.common import Choice, InquirerControl, create_inquirer_layout
from questionary.question import Question
from questionary.styles import merge_styles_default

from onec_gen.consts import SELECT_INSTRUCTION


def select_with_compact_answer(
    message: str,
    *,
    choices: list[Choice],
    answer_formatter: Callable[[Any], str],
    instruction: str = SELECT_INSTRUCTION,
    pointer: str | None = DEFAULT_SELECTED_POINTER,
    style: Style | None = None,
    use_indicator: bool = True,
) -> Question:
    merged_style = merge_styles_default([style])
    inquirer_control = InquirerControl(
        choices,
        pointer=pointer,
        use_indicator=use_indicator,
        use_shortcuts=False,
        show_selected=False,
        show_description=True,
        use_arrow_keys=True,
        initial_choice=None,
    )

    def get_prompt_tokens() -> list[tuple[str, str]]:
        tokens = [
            ("class:qmark", DEFAULT_QUESTION_PREFIX),
            ("class:question", f" {message}"),
        ]

        if inquirer_control.is_answered:
            selected_value = inquirer_control.get_pointed_at().value
            tokens.append(("class:answer", f" {answer_formatter(selected_value)}"))
        else:
            tokens.append(("class:instruction", f" {instruction}"))

        return tokens

    layout = create_inquirer_layout(
        inquirer_control,
        get_prompt_tokens,
    )
    bindings = build_select_bindings(inquirer_control)

    return Question(
        Application(
            layout=layout,
            key_bindings=bindings,
            style=merged_style,
            **utils.used_kwargs({}, Application.__init__),
        ),
    )


def build_select_bindings(inquirer_control: InquirerControl) -> KeyBindings:
    bindings = KeyBindings()

    @bindings.add(Keys.ControlQ, eager=True)
    @bindings.add(Keys.ControlC, eager=True)
    def abort(event: Any) -> None:
        event.app.exit(exception=KeyboardInterrupt, style="class:aborting")

    def move_cursor_down(_: Any) -> None:
        inquirer_control.select_next()
        while not inquirer_control.is_selection_valid():
            inquirer_control.select_next()

    def move_cursor_up(_: Any) -> None:
        inquirer_control.select_previous()
        while not inquirer_control.is_selection_valid():
            inquirer_control.select_previous()

    for key in (Keys.Down, "j", Keys.ControlN):
        bindings.add(key, eager=True)(move_cursor_down)

    for key in (Keys.Up, "k", Keys.ControlP):
        bindings.add(key, eager=True)(move_cursor_up)

    @bindings.add(Keys.ControlM, eager=True)
    def set_answer(event: Any) -> None:
        inquirer_control.is_answered = True
        event.app.exit(result=inquirer_control.get_pointed_at().value)

    @bindings.add(Keys.Any)
    def other(event: Any) -> None:
        return None

    return bindings
