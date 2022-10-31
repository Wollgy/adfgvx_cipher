"""
@author: libor_komanek
"""
import itertools
import sys
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QMessageBox
from unidecode import unidecode
from string import ascii_uppercase, digits
import random
from bidict import bidict

qtCreatorFile = "ADFGVXCipher.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

lang_replacements: dict[str, list[str]] = {  # "language": ["what is replaced", "what it's replaced with"]
    "en": ["J", "I"],
    "cs": ["Q", "KJU"]
}
space_representation: str = "XSPEACEX"
digit_representations: bidict[str, str] = bidict({  # two-way dictionary for converting digits to words and vice versa
    "0": "XZEROX",
    "1": "XONEX",
    "2": "XTWOX",
    "3": "XTHREEX",
    "4": "XFOURX",
    "5": "XFIVEX",
    "6": "XSIXX",
    "7": "XSEVENX",
    "8": "XEIGHTX",
    "9": "XNINEX"
})
adfgx_headers: bidict[int, str] = bidict({0: "A", 1: "D", 2: "F", 3: "G", 4: "X"})
adfgvx_headers: bidict[int, str] = bidict({0: "A", 1: "D", 2: "F", 3: "G", 4: "V", 5: "X"})


def replaceLanguageSpecificCharacters(text: str, lang: str, remove: bool = False) -> str:
    """Replaces a characters in the given string with their defined replacements based on specified language.
    Raises Exception if the provided language is not a valid value.

    :param text: original text
    :param lang: language specifying which characters are to be replaced; valid values are "en" and "cs"
    :param remove: whether the characters should be removed rather than replaced, defaults to False
    :return: string with replaced or removed characters for the specified language
    """
    if lang is None:
        return text
    text = text.upper()
    if lang in lang_replacements:
        return text.replace(
            lang_replacements[lang][0],
            lang_replacements[lang][1] if remove is False else "")
    else:
        raise ValueError("Invalid language specified.")


def filterMatrixData(adfgx: bool, data: str, lang: str = None) -> str:
    """Returns filtered data after making sure they are valid for matrix generation.

    :param adfgx: whether the basic version of the cipher is used
    :param data: the matrix data in the form of a string
    :param lang: language used for adfgx matrix generation
    :return: filtered matrix data
    """
    data = unidecode(data).upper()
    data = "".join(dict.fromkeys(data))
    if adfgx is True:
        if lang is not None:
            if lang not in lang_replacements:
                raise ValueError("Invalid Language speficied. filter")
            replaced_char = lang_replacements[lang][0]
            if replaced_char in data:
                raise ValueError(f"The matrix data contains '{replaced_char}' which cannot be used with the "
                                 f"specified language.")
            data = replaceLanguageSpecificCharacters(data, lang, True)
        data = "".join(char for char in data if char.isalpha())
        if len(data) != 25:
            raise ValueError("The matrix data needs to have exactly 25 unique characters and only contain letters!")
    else:
        data = "".join(char for char in data if char.isalnum())
        if len(data) != 36:
            raise ValueError(
                "The matrix data needs to have exactly 36 unique characters and only contain letters and digits!")
    return data


def generateMatrix(adfgx: bool, data: str = None, lang: str = None) -> list[list[str]]:
    """Generates either a random new matrix or uses the given data to generate one.

    This function is capable of generating a 5x5 matrix for the adfgx cipher or a 6x6 matrix for
    the extended adfgvx cipher.

    :param adfgx: whether the basic version of the cipher is used
    :param data: the matrix data in the form of a string
    :param lang: language used for adfgx matrix generation
    :return:
    """
    if data is None:  # generate random data
        data = ascii_uppercase
        if adfgx is True:
            data = replaceLanguageSpecificCharacters(data, lang)
            data = "".join(dict.fromkeys(data))
        else:
            data += digits
        data = "".join(random.sample(data, len(data)))
    else:  # validate the data is valid
        data = filterMatrixData(adfgx, data, lang)

    # create a matrix from the data
    size: int = (5 if adfgx is True else 6)  # 5x5 or 6x6 matrix
    matrix: list[list[str]] = [[data[i + size * j] for i in range(size)] for j in range(size)]
    return matrix


def convertCharacterRepresentations(text: str, adfgx: bool = False, reverse: bool = False) -> str:
    """Converts characters in the given text to their representations. Can also reverse the conversions back.

    Converts digits and spaces if the basic ADFGX cipher is used, otherwise only spaces are converted.

    :param text: the text to be modified
    :param adfgx: whether the basic version of the cipher is used
    :param reverse: whether the process of conversion should be reversed
    :return: modified text with possible representations of certain characters
    """
    text = (  # convert spaces
        text.replace(" ", space_representation)
        if reverse is False else
        text.replace(space_representation, " ")
    )
    if adfgx is True:  # convert digits if the 5x5 matrix is used
        if reverse is False:
            text = "".join(digit_representations[char] if char.isdigit() else char for char in text)
        else:
            for representation in digit_representations.inverse:
                text = text.replace(representation, digit_representations.inverse[representation])
    return text


def filterKeyword(keyword: str, input_len: int) -> str:
    """Returns filtered keyword after making sure it's valid.

    :param keyword: the raw keyword
    :param input_len: the lenght of the input text this key will be used with
    :return: filtered keyword
    """
    keyword = unidecode(keyword).upper().strip()
    keyword = "".join(char for char in keyword if char.isalpha())
    keyword = "".join(dict.fromkeys(keyword))  # remove duplicate characters
    if len(keyword) > input_len:  # the keyword cannot be longer than the text it's supposed to work with
        raise ValueError(f"The keyword is too long! "
                         f"Considering your input, it cannot be longer than {input_len} characters!")
    return keyword


def encodeCharacter(char: str, matrix: list[list[str]]) -> str:
    """Finds the two letters describing the position of the given character in the given matrix and returns them
    in the form of a string.

    :param char: character to be encoded
    :param matrix: matrix to be searched
    :return: string made up of two characters
    """
    for row in range(len(matrix)):
        if char in matrix[row]:
            col = matrix[row].index(char)
            # decide if afgx or afgvx headers should be used
            descriptors = (adfgvx_headers if len(matrix) == 6 else adfgx_headers)
            return f"{descriptors[row]}{descriptors[col]}"
    raise Exception("The character couldn't be found in the matrix during encoding.")


def decodeCharacter(pair: str, matrix: list[list[str]]) -> str:
    """Uses the two letters describing a character's position in the given matrix and returns the character.

    :param pair: a pair of letters describing a character's position in the matrix
    :param matrix: the matrix to be searched
    :return: character at the given position
    """
    descriptors = (adfgvx_headers if len(matrix) == 6 else adfgx_headers)
    row, col = descriptors.inverse[pair[0]], descriptors.inverse[pair[1]]
    char = matrix[row][col]
    return char


def filterPlainText(plaintext: str, lang: str = None, adfgx: bool = False) -> str:
    """Returns filtered plaintext prepared for encryption.

    :param plaintext: the raw plaintext
    :param lang: language used for adfgx matrix generation
    :param adfgx: whether the basic version of the cipher is used
    :return: filtered plaintext prepared for encryption
    """
    plaintext = unidecode(plaintext).upper().strip()
    plaintext = convertCharacterRepresentations(plaintext, adfgx)
    plaintext = "".join(char for char in plaintext if char.isalnum())  # get rid of special characters
    if adfgx is True:
        plaintext = replaceLanguageSpecificCharacters(plaintext, lang)
    return plaintext


def filterCipherText(ciphertext: str, adfgx: bool = False):
    """Returns filtered ciphertext prepared for decryption after making sure it's valid.

    :param ciphertext: the raw ciphertext
    :param adfgx: whether the basic version of the cipher is used
    :return: filtered ciphertext prepared for decryption
    """
    ciphertext = unidecode(ciphertext).upper().strip()
    ciphertext = "".join(char for char in ciphertext if char.isalpha() or char == " ")
    if len(ciphertext.replace(" ", "")) % 2 > 0:
        raise ValueError("The provided ciphertext is invalid! The number of characters is incorrect!")
    headers = (adfgx_headers if adfgx is True else adfgvx_headers)
    for char in ciphertext:
        if char not in headers.inverse and char != " ":
            raise ValueError("The provided ciphertext is invalid!")
    return ciphertext


def encrypt(plaintext: str,
            keyword: str,
            lang: str,
            matrix: list[list[str]] or str,
            adfgx: bool = False) -> str:
    """Encrypts a plaintext using the ADFGVX cipher or its simpler ADFGX version.

    :param plaintext: message to be encrypted
    :param keyword: keyword used for encryption
    :param lang: language used for adfgx matrix generation
    :param matrix: the cipher table in the form of a 2D list or a string with data
    :param adfgx: whether the basic version of the cipher is used
    :return: ciphertext
    """
    plaintext = filterPlainText(plaintext, lang, adfgx)
    if matrix is str:
        generateMatrix(adfgx, matrix, lang)
    encoded_text: str = "".join(encodeCharacter(char, matrix) for char in plaintext)  # encode characters in plaintext
    keyword = filterKeyword(keyword, len(encoded_text))

    # Create keyword grid (columnar transppsition)
    keyword_len, encoded_len = len(keyword), len(encoded_text)
    rows: int = int(encoded_len / keyword_len)
    keyword_grid = [
        [encoded_text[i + keyword_len * j] for i in range(keyword_len)]
        for j in range(rows)
    ]
    remainder: int = encoded_len % keyword_len
    if remainder > 0:  # append the remaining characters that don't take up the entire row
        keyword_grid.append([encoded_text[i] for i in range(rows * keyword_len, encoded_len)])
        # fill in empty strings to make it easier to work with
        [keyword_grid[-1].append("") for _ in range(keyword_len - remainder)]

    # Sort the keyword and columns in the keyword grid
    ciphertext = ""
    for i in sorted(keyword):
        ciphertext += "".join([keyword_grid[j][keyword.index(i)] for j in range(len(keyword_grid))])
        ciphertext += " "

    return ciphertext.strip()


def decrypt(ciphertext: str,
            keyword: str,
            lang: str,
            matrix: list[list[str]] or str,
            adfgx: bool = False) -> str:
    """Decrypts a ciphertext which was encrypted using the ADFGVX cipher or its simpler ADFGX version.

    Expects ciphertext to have individual columns divided by spaces and the columns to not have any extra characters
    to fill the empty positions.

    :param ciphertext: ciphertext to be decrypted
    :param keyword: keyword which was used for encryption
    :param lang: language used for adfgx matrix generation
    :param matrix: the cipher table that was used for encryption in the form of a 2D list or a string with data
    :param adfgx: whether the basic version of the cipher is used
    :return: original message
    """
    ciphertext: str = filterCipherText(ciphertext, adfgx)
    if matrix is str:
        generateMatrix(adfgx, matrix, lang)
    keyword = filterKeyword(keyword, len(ciphertext.replace(" ", "")))

    # Get encoded text
    ciphertext: list[str] = ciphertext.split()
    ciphertext: list[list[str]] = [[char for char in ciphertext[ciphertext.index(row)]] for row in ciphertext]
    keyword_sorted: list[str] = [i for i in sorted(keyword)]
    column_dict: dict[str, list[str]] = dict(zip(keyword_sorted, ciphertext))
    column_grid = [column_dict[char] for char in keyword]
    original_grid = list(map(list, itertools.zip_longest(*column_grid, fillvalue="")))  # encoded text in a 2D list
    encoded_text: str = "".join(char for row in original_grid for char in row).strip()

    # Convert encoded text to original plaintext
    plaintext: str = ""
    tmp: int = 0
    for i in range(2, len(encoded_text) + 1, 2):
        plaintext += decodeCharacter(encoded_text[tmp:i], matrix)
        tmp = i
    plaintext = convertCharacterRepresentations(plaintext, adfgx, True)  # convert character representations back

    return plaintext


class ADFGVXCipher(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowTitle("ADFG(V)X cipher")
        self.english_radio.setText(f"English ('{lang_replacements['en'][0]}' -> '{lang_replacements['en'][1]}')")
        self.czech_radio.setText(f"Czech ('{lang_replacements['cs'][0]}' -> '{lang_replacements['cs'][1]}')")

        self.matrix_55: list[list[str]] or None = None  # adfgx version
        self.matrix_66: list[list[str]] or None = None  # adfgvx version
        self.output: str or None = None  # default value

        self.button_execute.clicked.connect(self.execute)
        # ADFGX buttons
        self.button_generate_matrix_adfgx.clicked.connect(lambda: self.fillMatrix(True))
        self.button_input_matrix_adfgx.clicked.connect(lambda: self.fillMatrix(True, self.matrix_input_adfgx.text()))
        # ADFGVX buttons
        self.button_generate_matrix_adfgvx.clicked.connect(lambda: self.fillMatrix(False))
        self.button_input_matrix_adfgvx.clicked.connect(lambda: self.fillMatrix(False, self.matrix_input_adfgvx.text()))
        # Copy buttons
        self.button_copy_output.clicked.connect(self.copyOutput)
        self.button_copy_matrix.clicked.connect(self.copyMatrix)

    def execute(self):
        """Checks user input from GUI and calls execugtes appropriate code."""
        try:
            # Process values from GUI fields
            keyword: str = self.keyword.text()
            input_text: str = self.input_field.toPlainText()
            matrix: list[list[str]] or None = self.matrix_66
            use_adfgx: bool = False
            lang: str or None = None  # not required unless working with adfgx
            if self.tabWidget.currentIndex() == 0:  # adfgx version is used
                use_adfgx = True
                lang = ("en" if self.english_radio.isChecked() else "cs")
                matrix = self.matrix_55
            if len(keyword) < 1 or len(input_text) < 1:
                raise ValueError("You must enter a keyword and input text!")
            if matrix is None:
                raise Exception("You need to generate the matrix first!")

            # Proceed to encryption or decryption and update the output field in GUI with the result
            output_text: str = (
                encrypt(input_text, keyword, lang, matrix, use_adfgx)
                if self.encrypt_radio.isChecked()
                else decrypt(input_text, keyword, lang, matrix, use_adfgx))
            self.output = output_text
            self.output_field.setPlainText(output_text)
        except Exception as e:
            self.showErrorMessage(e)

    def fillMatrix(self, adfgx: bool, data: str = None) -> None:
        """Generates a matrix and fills the labels in GUI used to represent the cipher matrix with appropriate values.

        :param data: optional data to be used for matrix generation instead of random generation
        :param adfgx: whether the unextended version of the cipher should be used
        """
        try:
            # Generate the matrix
            lang: str or None = None
            version: str = "adfgvx"
            if adfgx is True:
                version = "adfgx"
                lang = ("en" if self.english_radio.isChecked() else "cs")
            matrix: list[list[str]] = generateMatrix(adfgx, data, lang)
            # Save the current matrix to be used during encryption or decryption
            if adfgx is True:
                self.matrix_55 = matrix
            else:
                self.matrix_66 = matrix
            # Update matrix values in GUI
            for row in range(len(matrix)):
                for col in range(len(matrix[row])):
                    self.findChild(QLabel, f"table_item_{row+1}{col+1}_{version}")\
                        .setText(matrix[row][col])
        except Exception as e:
            self.showErrorMessage(e)

    def copyOutput(self):
        """Copies the value of output property to clipboard."""
        try:
            clipboard = QApplication.clipboard()
            if self.output is None:
                raise Exception("There is no output to copy!")
            clipboard.setText(self.output)
        except Exception as e:
            self.showErrorMessage(e)

    def copyMatrix(self):
        """Copies matrix data in the form of a string to clipboard."""
        try:
            clipboard = QApplication.clipboard()
            matrix = self.matrix_66
            if self.tabWidget.currentIndex() == 0:
                matrix = self.matrix_55
            if matrix is None:
                raise Exception("There is not matrix to copy. Generate one first!")
            matrix: str = "".join(char for row in matrix for char in row)
            clipboard.setText(matrix)
        except Exception as e:
            self.showErrorMessage(e)

    @staticmethod
    def showErrorMessage(e: Exception) -> None:
        """Shows a popup message with information about an Exception.

        :param e: the exception that occurred
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Ooops!")
        msg.setText("Something went wrong!")
        msg.setInformativeText(str(e))
        msg.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ADFGVXCipher()
    window.show()
    sys.exit(app.exec())
