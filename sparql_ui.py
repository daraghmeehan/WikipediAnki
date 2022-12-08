import sys, typing
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5 import uic

# author: Daragh Meehan (S5420156)

class SPARQL_Query_UI(QWidget):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi("sparql_query.ui", self) # loads our UI file using PyQt5's uic method

        self.question = ""
        self.answer = ""

        # only enable these buttons when a question has been asked and an answer provided
        self.try_another_query_button.setEnabled(False)
        self.make_flashcard_button.setEnabled(False)

        # connecting buttons to our methods
        self.try_query_button.clicked.connect(self.try_query)
        self.try_another_query_button.clicked.connect(self.try_another_query)
        self.make_flashcard_button.clicked.connect(self.make_flashcard)

    def try_query(self) -> None:
        """This would take our user's question, call the translation and find the result from wikidata, and write the answer into the answer box"""

        # prevent changes to query once trying query
        self.question_box.setReadOnly(True)

        self.try_query_button.setEnabled(False)
        self.the_answer.setText("Finding answer...")

        self.question = self.question_box.text()

        ### do query here
        self.answer = "Sorry this doesn't work :("

        # setting answer in answer box
        self.the_answer.setText(self.answer)

        # allow user to go back and try a different query
        self.try_another_query_button.setEnabled(True)
        self.make_flashcard_button.setEnabled(True)

    def try_another_query(self) -> None:
        """Resets the question and answer, and default button settings, to try another query"""

        self.try_another_query_button.setEnabled(False)
        self.make_flashcard_button.setEnabled(False)

        self.question = ""
        self.answer = ""

        self.question_box.setText("")
        self.the_answer.setText("...")

        self.question_box.setReadOnly(False)

        self.try_query_button.setEnabled(True)

    def make_flashcard(self) -> tuple[str, str, str, str]:
        """Here we would return our flashcard fields and close the app"""
        pass


def query_wikidata_with_sparql() -> tuple[str, str, str, str]:
    """Opens our SPARQL UI and allows the user to input a query and returns the fields of our flashcard if an answer is found"""
    app = QApplication([])
    window = SPARQL_Query_UI()
    window.show()

    try:
        # unfortunately, we cannot return answers as our models didn't work
        app.exec_()
    except:
        # returning an empty card
        return "", "", "", ""


# for testing
if __name__ == "__main__":
    q, a = query_wikidata_with_sparql()
    print(q, a)
