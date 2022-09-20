import requests, spacy
from bs4 import BeautifulSoup

import pandas as pd  # for collecting our flashcards
import re  # for cleaning Wikipedia text
import ast  # for converting string representation of list to a list
import pyperclip  # for editing flashcards quickly by copying to the clipboard
import time  # for timestamping csv of flashcards
from pathlib import Path  # for writing flashcards to "Flashcards" folder

nlp = spacy.load("en_core_web_sm")  # loading the language model


def run_wikipedianki() -> None:

    print("\nWelcome to WikipediAnki!")

    flashcards = pd.DataFrame(columns=["Question", "Answer", "Hint", "Title", "URL"])

    still_studying = True

    try:
        while still_studying:

            # choose page
            wikipedia_url, soup = choose_page()
            if wikipedia_url == "b":
                # exit condition
                still_studying = False
                continue

            page_title = soup.find(id="firstHeading").text
            print(f'You have chosen the page "{page_title}"')

            # make cards
            new_cards = study_page(soup)

            # add extra page information to each card
            for card in new_cards:
                card["Title"] = page_title
                card["URL"] = wikipedia_url

            # add new cards to our collection
            new_cards = pd.DataFrame(new_cards)
            flashcards = pd.concat([flashcards, new_cards], ignore_index=True)

            # change page or exit
            print("\nWould you like to choose another page?")
            still_studying = confirm_with_user()

    except:
        print("Error encountered. Saving current flashcards and exiting...")

    # save to file
    print("\nFinished studying. Saving flashcards to .csv")
    save_flashcards_to_csv(flashcards)


# ask the user what Wikipedia page to learn from, and return the final URL and BeautifulSoup's soup object of the page
def choose_page() -> tuple[str, BeautifulSoup]:

    wikipedia_url = input(
        '\nWhat Wikipedia page do you want to learn from? Or input "b" to quit and save flashcards.\n'
    )

    if wikipedia_url == "b":
        return wikipedia_url, None

    try:
        r = requests.get(wikipedia_url, allow_redirects=True)
        soup = BeautifulSoup(r.content, "html.parser", from_encoding="utf-8")
        redirected_address = soup.find("link", rel="canonical").get("href")
        assert (
            wikipedia_url == redirected_address
        )  # if choose "Barack", we get redirected to "Barack Obama". Assert equal to make sure user has desired page, and using consistent naming of pages
    except:
        print(
            "Please try again with a valid Wikipedia page.\nThis includes the correct redirected address."
        )
        return choose_page()

    return wikipedia_url, soup


# using a given page's soup object, create new flashcards of user-selected sentences, returning a list of the new cards to add to our deck
def study_page(soup: BeautifulSoup) -> list[dict]:

    page_title = soup.find(
        id="firstHeading"
    ).text  # in case want to use title as answer

    text = retrieve_text(soup)

    doc = nlp(text)  # doing sentence splitting and tokenisation
    sents = list(doc.sents)  # all sentences are type spacy.tokens.span.Span

    new_cards = []
    still_creating_cards = True

    while still_creating_cards:

        try:
            next_card = create_next_card(sents, page_title)
        except:
            print("Error creating new cards. Saving current created cards.")
            return new_cards

        if next_card == {}:
            still_creating_cards = False
            continue

        new_cards.append(next_card)

    return new_cards


# retrieve the text of the given page, with basic preprocessing
def retrieve_text(soup: BeautifulSoup) -> spacy.tokens.doc.Doc:

    all_paragraphs = soup.find_all("p")[1:-1]  # first and last paragraphs are "\n"
    text = "\n".join([paragraph.text.strip() for paragraph in all_paragraphs])
    text = re.sub(r"\[[0-9]+\]", "", text)  # removing [1], [2] etc. from text

    return text


# given sentences of Wikipedia page, create new card from a user-selected sentence
def create_next_card(sents: list[spacy.tokens.span.Span], page_title: str) -> dict:

    next_card = {}

    sentence_substring = input(
        '\nType a substring of the sentence you want to make a flashcard for.\nEnter "b" to cancel.\n'
    )

    if sentence_substring == "b":
        print("Are you sure you want to stop making new cards?")
        if confirm_with_user():
            return next_card
        else:
            return create_next_card(sents, page_title)

    # simple way to find matching sentences
    matching_sents = [sent for sent in sents if sentence_substring in sent.text]

    if len(matching_sents) == 0:
        print("No matching sentences. Please try again.")
        return create_next_card(sents)

    if len(matching_sents) > 5:
        print(
            "More than 5 matching sentences. Please be more specific to narrow down your search."
        )
        return create_next_card(sents, page_title)

    line_number_to_learn = choose_line(matching_sents)
    if line_number_to_learn == -1:
        return create_next_card(sents, page_title)

    line_to_learn = matching_sents[line_number_to_learn - 1]

    next_card = create_card_from_line(line_to_learn, page_title)
    if next_card == {}:
        # if choose to not make a flashcard for this sentence, allow choosing a different sentence
        return create_next_card(sents, page_title)

    return next_card


# ask user which line of those that match the user's input they want to make a flashcard from
def choose_line(sents: list[spacy.tokens.span.Span]) -> int:

    print('\nChoose which line to learn from, or go back with "b".')

    for i in range(1, len(sents) + 1):
        print(f"{i}) {sents[i - 1]}")

    line_number_to_learn = input(
        '\nWhich line do you want to learn? Or go back with "b".\n'
    )

    if line_number_to_learn == "b":
        return -1
    else:
        line_number_to_learn = int(line_number_to_learn)

    if line_number_to_learn not in list(range(1, len(sents) + 1)):
        print("Please try again and choose a valid line.")
        return choose_line(sents)

    return line_number_to_learn


# the user determines what the card for the given line will look like, and the completed card is returned
def create_card_from_line(
    line_to_learn: spacy.tokens.span.Span, page_title: str
) -> dict:

    print("\nPlease choose from the words of the sentence.")
    # printing words of line
    for i in range(1, len(line_to_learn) + 1):
        print(f"{i} {line_to_learn[i - 1]}")

    selected_spans_str = input(
        f'\nSelect a span (e.g. "[1,2,3]"), a single word (e.g. "[5]"), or even a multiple spans (e.g. "[[1,2], [5,6]]")\nEnter "t" to use the page\'s title as the answer.\nEnter "b" to cancel.\n'
    )

    if selected_spans_str == "b":
        print("Still want to make a flashcard for this sentence?")
        if confirm_with_user():
            return create_card_from_line(line_to_learn, page_title)
        else:
            return {}

    elif selected_spans_str == "t":
        # use the page's title as the answer
        question = line_to_learn.text
        answer = page_title

    else:
        # otherwise need to parse the given spans and build the question and answers to print on the flashcard
        all_spans = []  # to track all the spans mentioned
        span_numbers = (
            {}
        )  # to track, for a given index, which span group (i.e. the answer) it corresponds to
        answers = []  # to collect the answers for the given sub_spans

        try:
            selected_spans = ast.literal_eval(selected_spans_str)
            assert isinstance(selected_spans, list)

            if isinstance(selected_spans[0], int):
                # if only have one span, e.g. "[1,2,3]" or "[5]"
                selected_spans = [
                    selected_spans
                ]  # can trivially treat as a nested span

            elif not isinstance(selected_spans[0], list):
                raise

            # now have a list of spans "[[1,2], [5,6]]", or simply "[[1,2,3]]"
            all_spans = [
                idx for sub_span in selected_spans for idx in sub_span
            ]  # simply extracting every word index from our list of lists
            for i, sub_span in enumerate(selected_spans, start=1):
                # now building answer for given sub_span, and assigning span numbers (corresponding answer) for each index of the sub-span
                answer = ""

                for j, idx in enumerate(sub_span, start=1):
                    span_numbers[
                        idx
                    ] = i  # assigns indiviual index to a specific span (answer), to use when creating the flashcard

                    if j != len(sub_span):
                        answer += line_to_learn[idx - 1].text_with_ws
                    else:
                        # don't add whitespace if at the last sub_span index (don't want an answer with a space at the end)
                        answer += line_to_learn[idx - 1].text

                answers.append(answer)

            question = ""
            for i in range(1, len(line_to_learn) + 1):
                token = line_to_learn[i - 1]
                if i in all_spans:
                    span_number = span_numbers[i]  # like a reverse dict search
                    question += f"[{span_number}]"
                    question += token.whitespace_
                else:
                    question += token.text_with_ws

            answer = ""
            for i, individual_answer in enumerate(answers, start=1):
                if i == len(answers):
                    answer += f"{i} {individual_answer}"
                else:
                    answer += f"{i} {individual_answer}\n"

        except:
            print("Please try again with a valid span.")
            return create_card_from_line(line_to_learn, page_title)

    # cleaning up whitespace inconsistencies with bs4 and spacy
    question = question.strip()
    answer = answer.strip()

    print_card_preview(question, answer)

    hint = ""

    print("\nDo you want to add a hint?")
    if confirm_with_user():
        hint = write_hint()
        hint = hint.replace("\\n", "\n")
        print_card_preview(question, answer, hint)

    print("\nFinally, would you like to edit any field?")
    if confirm_with_user():
        question, answer, hint = edit_fields(question, answer, hint)
        print_card_preview(question, answer)

    card = {"Question": question, "Answer": answer, "Hint": hint}

    print("\nSuccessfully created card.\n")

    return card


# the user writes what they would like their hint to be
def write_hint() -> str:

    hint = input(
        '\nPlease type your hint. Use "\\n" to create multiple line hints for multiple spans.\nEnter "b" to cancel.\n'
    )

    if hint in ["", "b"]:
        print("\nWant to skip making a hint?")
        if confirm_with_user():
            return ""
        else:
            return write_hint()
    else:
        return hint


# gives the user a preview of what their card will look like, so they can choose whether or not to make further changes
def print_card_preview(question: str, answer: str, hint="") -> None:

    print("\nThis is what your flashcard will look like:\n")
    print(f"Question:\n{question}")
    if hint != "":
        print(f"Hint:\n{hint}")
    print("----------")
    print(f"Answer:\n{answer}")


# allows the user to edit the fields of the flashcard in case they aren't happy
def edit_fields(question: str, answer: str, hint: str) -> tuple([str, str, str]):

    field = input(
        '\nWhich field would you like to edit?\n"q" for question, "a" for answer, "h" for hint, "b" to cancel.\n'
    )

    if field not in ["q", "a", "h", "b"]:
        return edit_fields(question, answer, hint)

    elif field == "b":
        return question, answer, hint

    elif field == "q":
        pyperclip.copy(question)
        print(f"\nQuestion was: {question}, which has been copied to the clipboard.\n")
        new_question = input(
            'Enter "b" to cancel the operation. Replace question with:\n'
        )
        if new_question == "b":
            return edit_fields(question, answer, hint)
        else:
            question = new_question

    elif field == "a":
        pyperclip.copy(answer)
        print(f"\nAnswer was: {answer}, which has been copied to the clipboard.\n")
        new_answer = input('Enter "b" to cancel the operation. Replace answer with:\n')
        if new_answer == "b":
            return edit_fields(question, answer, hint)
        else:
            answer = new_answer

    else:
        pyperclip.copy(hint)
        print(f"\nHint was: {hint}, which has been copied to the clipboard.\n")
        new_hint = input('Enter "b" to cancel the operation. Replace hint with:\n')
        if new_hint == "b":
            return edit_fields(question, answer, hint)
        else:
            hint = new_hint

    print("Finished editing?")
    if confirm_with_user():
        return question, answer, hint
    else:
        return edit_fields(question, answer, hint)


# simple function to confirm choices with the user
def confirm_with_user() -> bool:

    y_or_n = input("[y/n] ")
    if y_or_n == "y":
        return True
    elif y_or_n == "n":
        return False
    else:
        return confirm_with_user()


# saves all the flashcards we have created to a csv, which allows easy importing into Anki
def save_flashcards_to_csv(flashcards: pd.core.frame.DataFrame) -> None:

    number_of_cards = len(flashcards.index)
    if number_of_cards == 0:
        print("No cards created. Quitting without saving.")
        return

    timestamp = time.strftime("%d-%m-%Y_%H%M%S", time.localtime())
    file_name = f"{timestamp} - {number_of_cards} cards"
    file_path = Path(f"./Flashcards/{file_name}.csv")
    file_path.parent.mkdir(
        exist_ok=True
    )  # making the "Flashcard" directory if we don't have it

    flashcards.to_csv(file_path, columns=flashcards.columns, header=False, index=False)


if __name__ == "__main__":

    run_wikipedianki()
