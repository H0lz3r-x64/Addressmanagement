import datetime, cv2, sys, shutil
import os, platform, ctypes

import mysql.connector
import reportlab.pdfgen.canvas
from reportlab.pdfgen import canvas

import PyQt6
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from Ui_Adressverwaltung_Hauptfenster import Ui_Hauptfenster

os.environ["QT_FONT_DPI"] = "115"


def DB_verbinden():
    DB_String = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'test'
    }
    # SQL-Verbindung herstellen, Fehlerbehandlung
    try:
        global mydb
        mydb = mysql.connector.connect(**DB_String)
        global mycursor
        mycursor = mydb.cursor()
    except mysql.connector.errors.Error:
        print("Es konnte keine Verbindung zur Server-Datenbank hergestellt werden!")
        exit(0)


def DB_schliessen():
    if mydb.is_connected():
        mycursor.close()
        mydb.close()
        print("MySQL Verbindung wurde geschlossen")


def last_edited():
    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M:%S - %d/%m/%Y")
    return current_time


class Main(QMainWindow, Ui_Hauptfenster):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # load modes
        self.light_mode = app.palette()
        self.dark_mode = self.load_darkstyle()

        # load save_file and set mode
        f = open("./save_file.txt", 'r')
        self.current_mode = f.read()
        f.close()
        if self.current_mode == "dark":
            app.setPalette(self.dark_mode)
            self.mode_select.setIcon(QIcon(r".\Resources\Icons\own\darkmode.png"))
        else:
            app.setPalette(self.light_mode)
            self.mode_select.setIcon(QIcon(r".\Resources\Icons\own\lightmode.png"))

        # needed variables
        self.new_element = False
        self.path = str()
        self.no_pic_path = r".\Resources\Icons\own\NoPortrait.png"
        self.last_selected_row = 0

        # toolTip
        self.lblPic_searchInfo.setToolTipDuration(6 ** 10)
        self.lblPic_searchInfo.setToolTip(
            "Durchsucht die Datenbank nach eingegebenem Wert in den Feldern: \n"
            "Firma, Nachname, Vorname, Geburtsdatum\n\nSuche direkt nach einem Index indem ein \"#\" "
            "vorangesetzt wird.\nzB: #1")

        # run methods
        self.organization()
        self.tabelle_generieren()

        # if no entry in database
        if self.Daten_Tabelle.rowCount() == 0:
            self.first_element()

        # Debug | auto Input
        # i = 0
        # while i < 12222:
        #     self.on_pb_neuer_eintrag_clicked()
        #     self.VOR_NAMEN.setText(f"autoInp{i}")
        #     self.FAM_NAME.setText(f"{i}")
        #     self.on_SPEICHERN_AENDERN_clicked()
        #     i += 1

    # ------------------------------------------------------------------------------------------------------------------
    # Methoden

    def load_darkstyle(self):
        app.setStyle("fusion")

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(100, 105, 120))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(90, 90, 90))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, QColor(90, 90, 90))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Link, QColor(90, 90, 90))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.BrightText, QColor(90, 90, 90))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(90, 90, 90))
        return palette

    def tabelle_generieren(self):
        # Überschrift ausgeben
        self.Daten_Tabelle.setColumnCount(20)
        column = QTableWidgetItem("ID")
        self.Daten_Tabelle.setHorizontalHeaderItem(0, column)
        column = QTableWidgetItem("Organisation")
        self.Daten_Tabelle.setHorizontalHeaderItem(1, column)
        column = QTableWidgetItem("Nachname")
        self.Daten_Tabelle.setHorizontalHeaderItem(2, column)
        column = QTableWidgetItem("Vorname")
        self.Daten_Tabelle.setHorizontalHeaderItem(3, column)
        column = QTableWidgetItem("Titel-1")
        self.Daten_Tabelle.setHorizontalHeaderItem(4, column)
        column = QTableWidgetItem("Titel-2")
        self.Daten_Tabelle.setHorizontalHeaderItem(5, column)
        column = QTableWidgetItem("Titel-3")
        self.Daten_Tabelle.setHorizontalHeaderItem(6, column)
        column = QTableWidgetItem("Geburtsdatum")
        self.Daten_Tabelle.setHorizontalHeaderItem(7, column)
        column = QTableWidgetItem("Straße")
        self.Daten_Tabelle.setHorizontalHeaderItem(8, column)
        column = QTableWidgetItem("Haus-Nr.")
        self.Daten_Tabelle.setHorizontalHeaderItem(9, column)
        column = QTableWidgetItem("Ort")
        self.Daten_Tabelle.setHorizontalHeaderItem(10, column)
        column = QTableWidgetItem("PLZ")
        self.Daten_Tabelle.setHorizontalHeaderItem(11, column)
        column = QTableWidgetItem("Land")
        self.Daten_Tabelle.setHorizontalHeaderItem(12, column)
        column = QTableWidgetItem("LKZ")
        self.Daten_Tabelle.setHorizontalHeaderItem(13, column)
        column = QTableWidgetItem("E-Mail gesch.")
        self.Daten_Tabelle.setHorizontalHeaderItem(14, column)
        column = QTableWidgetItem("Tel.Nr. gesch.")
        self.Daten_Tabelle.setHorizontalHeaderItem(15, column)
        column = QTableWidgetItem("Mobil Nr.")
        self.Daten_Tabelle.setHorizontalHeaderItem(16, column)
        column = QTableWidgetItem("Anzahl Kinder")
        self.Daten_Tabelle.setHorizontalHeaderItem(17, column)
        column = QTableWidgetItem("Portrait")
        self.Daten_Tabelle.setHorizontalHeaderItem(18, column)
        column = QTableWidgetItem("Zuletzt Geändert")
        self.Daten_Tabelle.setHorizontalHeaderItem(19, column)

        self.aktualisieren()

    def first_element(self):
        DB_verbinden()
        sql = "ALTER TABLE addresses AUTO_INCREMENT = 1"
        mycursor.execute(sql)
        DB_schliessen()
        self.new_element = True
        self.last_selected_row = 1
        new_row_count = self.Daten_Tabelle.rowCount() + 1
        new_id = 1
        self.Daten_Tabelle.setRowCount(new_row_count)
        self.Daten_Tabelle.setItem(new_row_count - 1, 0, QTableWidgetItem(str(new_id)))
        self.Daten_Tabelle.selectRow(new_row_count - 1)
        self.Daten_Tabelle.setEnabled(False)
        self.LOESCHEN.setEnabled(False)
        self.pb_neuer_eintrag.setEnabled(False)

    # ------------------------------------------------------------------------------------------------------------------
    # Slots & Signale

    def keyPressEvent(self, e):
        if e.key() == PyQt6.QtCore.Qt.Key.Key_F5:
            self.aktualisieren()

    @pyqtSlot()
    def on_SPEICHERN_AENDERN_clicked(self):
        print("Daten speichern")
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape(0)))  # cursor wird zu einer Sanduhr gesetzt.
        self.SPEICHERN_AENDERN.setEnabled(False)  # Button wird disabled
        self.last_selected_row = self.Daten_Tabelle.currentRow()
        self.speichern()
        self.Daten_Tabelle.selectRow(self.last_selected_row)
        self.SPEICHERN_AENDERN.setEnabled(True)  # Button wird disabled
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape(0)))

    @pyqtSlot()
    def on_mode_select_clicked(self):
        if self.current_mode == "light":
            self.mode_select.setIcon(QIcon(r".\Resources\Icons\own\darkmode.png"))
            app.setPalette(self.dark_mode)
            self.current_mode = "dark"
        else:
            self.mode_select.setIcon(QIcon(r".\Resources\Icons\own\lightmode.png"))
            app.setPalette(self.light_mode)
            self.current_mode = "light"

        f = open("./save_file.txt", 'w')
        f.write(self.current_mode)
        f.close()

    @pyqtSlot()
    def on_LOESCHEN_clicked(self):
        print("löschen")
        # Message Box
        msg = QMessageBox()
        msg.setWindowTitle("Achtung!")
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setText("Ausgewählten Eintrag wirklich löschen?")
        msg.setInformativeText("Kann nicht rückgängig gemacht werden")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        x = msg.exec()
        if x == QMessageBox.StandardButton.Yes:
            self.loeschen()

    @pyqtSlot(str)
    def on_le_Suche_textChanged(self):
        print("Suche")
        self.suchen()

    @pyqtSlot()
    def on_le_Suche_editingFinished(self):
        self.suchen()

    @pyqtSlot()
    def on_pb_neuer_eintrag_clicked(self):
        if not self.new_element:
            self.last_selected_row = self.Daten_Tabelle.currentRow()
            self.new_element = True
            new_row_count = self.Daten_Tabelle.rowCount() + 1
            new_id = int(self.Daten_Tabelle.item(self.Daten_Tabelle.rowCount() - 1, 0).text()) + 1
            self.Daten_Tabelle.setRowCount(new_row_count)
            self.Daten_Tabelle.setItem(new_row_count - 1, 0, QTableWidgetItem(str(new_id)))
            self.Daten_Tabelle.selectRow(new_row_count - 1)
            self.Daten_Tabelle.setEnabled(False)
            self.LOESCHEN.setEnabled(False)
            self.pb_neuer_eintrag.setText("Abbrechen")
        else:
            self.pb_neuer_eintrag.setText("Neuer Eintrag")
            self.new_element = False
            self.aktualisieren()
            self.Daten_Tabelle.selectRow(self.last_selected_row)
            self.pb_neuer_eintrag.setEnabled(True)
            self.Daten_Tabelle.setEnabled(True)
            self.LOESCHEN.setEnabled(True)

    @pyqtSlot()
    def on_FIRMA_BOX_clicked(self):
        self.organization()

    @pyqtSlot()
    def on_PRIVAT_BOX_clicked(self):
        self.organization()

    @pyqtSlot(QTableWidgetItem, QTableWidgetItem)
    def on_Daten_Tabelle_currentItemChanged(self, current, previous):
        self.index_aendern()

    @pyqtSlot()
    def on_pb_photo_clicked(self):
        self.pb_photo.setEnabled(False)
        # Message Box
        msg = QMessageBox()
        msg.setWindowTitle("Kamera öffnen?")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText("Klicke \"Open\" um die Kamera zu starten.")
        msg.setInformativeText("Das laden des Kamera Moduls kann einige Sekunden in Anspruch nehmen..")
        msg.setStandardButtons(QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Abort)
        msg.setDefaultButton(QMessageBox.StandardButton.Open)
        x = msg.exec()
        if x == QMessageBox.StandardButton.Open:
            self.photo()

        self.pb_photo.setEnabled(True)

    @pyqtSlot()
    def on_pb_upload_clicked(self):
        self.pb_upload.setEnabled(False)
        self.upload()
        self.pb_upload.setEnabled(True)

    @pyqtSlot()
    def on_pb_bild_entfernen_clicked(self):
        self.delete_picture()

    def organization(self):
        if self.PRIVAT_BOX.isChecked():
            self.FIRMEN_NAME.setEnabled(False)
            print("s")
            return "Privat"
        elif self.FIRMA_BOX.isChecked():
            self.FIRMEN_NAME.setEnabled(True)
            return self.FIRMEN_NAME.text()

    def geb_datum(self):
        if self.GEB_DATUM.text() == "31.12.9999":
            return ''
        else:
            now = datetime.datetime.now()
            return self.GEB_DATUM.date().toString('dd/MM/yyyy')

    def speichern(self):
        DB_verbinden()  # Verbindung zur DB herstellen
        if self.organization() != '' and self.FAM_NAME.text() != '' and self.VOR_NAMEN.text() != '':
            # Wähle die Spalten aus
            print("Wähle die Spalten aus\n")
            if self.new_element:
                print("new element")
                val = str(int(self.Daten_Tabelle.item(self.Daten_Tabelle.rowCount() - 1, 0).text()) + 1)
                print(val)
            else:
                print("normal element")
                val = self.Daten_Tabelle.item(self.Daten_Tabelle.currentRow(), 0).text()

            print("ID: " + val)
            sql = "SELECT * FROM addresses WHERE `ID` IN (" + val + ")"
            mycursor.execute(sql)  # führe den Befehl aus
            fetch = mycursor.fetchall()

            # Überprüfung ob Eintrag vorhanden oder nicht. Dann wird in DB geschrieben bzw. geändert.
            if len(fetch) == 0:  # Kein Eintrag gefunden
                print("Eintrag nicht vorhanden")

                sql = "INSERT INTO `addresses`(`PRV_FIR`, `FAM_NAME`, `VOR_NAMEN`, `TITEL_1`, " \
                      "`TITEL_2`, `TITEL_3`, `GEB_DATUM`, `STR`, `STR_NR`, `ORT`, `PLZ`, `LAND`, `LKZ`, " \
                      "`GESCH_MAIL`, `GESCH_NR`, `MOBIL_NR`, `ANZ_KINDER`, `PORTRAIT`, `LAST_EDITED`) " \
                      "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

                val = (self.organization(), self.FAM_NAME.text(), self.VOR_NAMEN.text(),
                       self.TITEL1.currentText(), self.TITEL2.currentText(), self.TITEL3.currentText(),
                       self.geb_datum(), self.STR.text(), self.STR_NR.text(), self.ORT.text(), self.PLZ.text(),
                       self.LAND.currentText(), self.LKZ.text(), self.GESCH_MAIL.text(), self.GESCH_VOR.text() +
                       " " + self.GESCH_NR.text(), self.MOBIL_VOR.text() + " " + self.MOBIL_NR.text(),
                       self.ANZ_KINDER.text(), self.path, last_edited())

            else:  # Eintrag bereits vorhanden
                print("Eintrag bereits vorhanden")

                sql = "UPDATE `addresses` SET `PRV_FIR`=%s, `FAM_NAME`=%s, `VOR_NAMEN`=%s, `TITEL_1`=%s, " \
                      "`TITEL_2`=%s,`TITEL_3`=%s, `GEB_DATUM`=%s, `STR`=%s,`STR_NR`=%s,`ORT`=%s,`PLZ`=%s, " \
                      "`LAND`=%s,`LKZ`=%s,`GESCH_MAIL`=%s, `GESCH_NR`=%s,`MOBIL_NR`=%s, `ANZ_KINDER`=%s, " \
                      "`PORTRAIT`=%s, `LAST_EDITED`=%s WHERE `ID` IN (" + val + ")"

                val = (self.organization(), self.FAM_NAME.text(), self.VOR_NAMEN.text(), self.TITEL1.currentText(),
                       self.TITEL2.currentText(), self.TITEL3.currentText(), self.geb_datum(), self.STR.text(),
                       self.STR_NR.text(), self.ORT.text(), self.PLZ.text(), self.LAND.currentText(),
                       self.LKZ.text(), self.GESCH_MAIL.text(), self.GESCH_VOR.text() +
                       " " + self.GESCH_NR.text(), self.MOBIL_VOR.text() + " " + self.MOBIL_NR.text(),
                       self.ANZ_KINDER.text(), self.path, last_edited()
                       )
            # ------------------------------
            mycursor.execute(sql, val)
            print(sql, val)
            mydb.commit()
            print("Daten erfolgreich in DB eingetragen / geändert.")
            if self.new_element:
                self.pb_neuer_eintrag.click()
            else:
                self.aktualisieren()

        else:
            # Message Box
            msg = QMessageBox()
            msg.setWindowTitle("Speichern fehlgeschlagen")
            msg.setWindowIcon(QIcon(r".\Resources\Icons\computer\W95MBX01.ICO"))
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Eines der folgenden Felder ist nicht befüllt:")
            msg.setInformativeText("Firma/Privat\nVorname\nNachname")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.setDefaultButton(QMessageBox.StandardButton.Ok)
            x = msg.exec()

        DB_schliessen()

    def loeschen(self):
        DB_verbinden()  # Verbindung zur DB herstellen
        print("current row", self.Daten_Tabelle.currentRow())
        try:
            id = self.Daten_Tabelle.item(self.Daten_Tabelle.currentRow(), 0).text()
            print(id)
            sql = "DELETE FROM `addresses` WHERE `ID` IN (" + id + ")"
            mycursor.execute(sql)
            mydb.commit()
            self.aktualisieren()
        except Exception as e:
            print(e)
        DB_schliessen()

    def suchen(self):
        if self.le_Suche.text() != '':
            DB_verbinden()  # Verbindung zur DB herstellen

            val = self.le_Suche.text()
            print(val)

            if self.le_Suche.text().startswith('#'):
                # Bei "#" an erster Stelle wird nur die genaue ID gesucht
                if len(self.le_Suche.text()) > 1:
                    try:
                        sql = "SELECT * FROM `addresses` WHERE `ID` IN (" + val[1:] + ")"
                    except Exception as e:
                        print(e)
                else:
                    print("Warte auf weiteres Zeichen hinter \"#\"")
            # allgemeine Suche
            else:
                sql = "SELECT * FROM `addresses` WHERE `PRV_FIR` LIKE ('%" + val + "%') OR `FAM_NAME` LIKE " \
                                                                                   "('%" + val + "%') OR `VOR_NAMEN` LIKE ('%" + val + "%') OR `GEB_DATUM` LIKE ('%" + val + "%')"
            try:
                mycursor.execute(sql)

                found = mycursor.fetchall()
                print("Elements found: " + str(len(found)))
                self.lbl_ElementsFound.setText(f"Einträge gefunden: {str(len(found))}")

                zeile = 0
                z, s = 0, 0
                for z in found:  # Zeilen auslesen und ausgeben
                    for s in range(0, 20):  # Spalten auslesen und ausgeben
                        self.Daten_Tabelle.setRowCount(zeile + 1)
                        fielditem = QTableWidgetItem(str(z[s]))  # konvertiert zu String
                        self.Daten_Tabelle.setItem(zeile, s, fielditem)
                    zeile += 1
                print("Adressen werden in Tabelle angezeigt")
            except Exception as e:
                print(e)
            DB_schliessen()
            self.Daten_Tabelle.selectRow(0)
        else:
            self.aktualisieren()

    def index_aendern(self):
        print("index_aendern")
        index = self.Daten_Tabelle.currentRow()
        id = self.Daten_Tabelle.item(index, 0).text()
        print(id)
        self.lbl_IndexSelected.setText(f"Index: {index}     ID: {id}")
        try:
            if self.new_element:
                print("new_element")
                fromDB = [''] * 20
            else:
                print("not new_element")
                DB_verbinden()  # Verbindung zur DB herstellen

                sql = "SELECT * FROM addresses WHERE `ID` IN (" + id + ")"
                mycursor.execute(sql)
                fetch = mycursor.fetchall()
                fromDB = fetch[0]

            self.lbl_lastEdited.setText(f"Zuletzt bearbeitet: {fromDB[19]}")
            # ---------------------------
            filled = 0
            empty = 0
            for f in fromDB:
                if f != '':
                    filled += 1
                else:
                    empty += 1
            self.lbl_filledInData.setText(f"Ausgefüllte Daten: {filled}/{filled + empty}")
            # ---------------------------
            self.FAM_NAME.setText(fromDB[2]), self.VOR_NAMEN.setText(fromDB[3]), self.TITEL1.setCurrentText(fromDB[4])
            self.TITEL2.setCurrentText(fromDB[5]), self.TITEL3.setCurrentText(fromDB[6]), self.STR.setText(fromDB[8])
            self.STR_NR.setText(fromDB[9]), self.ORT.setText(fromDB[10]), self.PLZ.setText(str(fromDB[11]))
            self.LKZ.setText(fromDB[13]), self.GESCH_MAIL.setText(fromDB[14])

            if fromDB[15] != "":
                strings = fromDB[15].split(" ")
                self.GESCH_VOR.setText((strings[0]))
                self.GESCH_NR.setText(strings[1])
            else:
                self.GESCH_VOR.setText(""), self.GESCH_NR.setText("")

            if fromDB[16] != "":
                strings = fromDB[16].split(" ")
                self.MOBIL_VOR.setText((strings[0]))
                self.MOBIL_NR.setText(strings[1])
            else:
                self.MOBIL_VOR.setText(""), self.MOBIL_NR.setText("")

            try:
                self.GEB_DATUM.setDate(QDate.fromString(fromDB[7]))
            except:
                self.GEB_DATUM.setDate(QDate(31, 12, 9999))

            if fromDB[17] != '':
                self.ANZ_KINDER.setValue(int(fromDB[17]))
            else:
                self.ANZ_KINDER.setValue(0)

            # portrait
            if fromDB[18] != '':
                self.path = fromDB[18]
            else:
                self.path = self.no_pic_path
            print(f"portrait file: {self.path}")
            self.lbl_portrait.setPixmap(QPixmap(self.path))

            if fromDB[12] != '':
                self.LAND.setCurrentText(fromDB[12])
        except Exception as e:
            print(e)

    def delete_picture(self):
        self.path = self.no_pic_path
        self.lbl_portrait.setPixmap(QPixmap(self.path))

    def upload(self):
        index = self.Daten_Tabelle.currentRow()
        if self.Daten_Tabelle.rowCount() < 1:
            id = 1
        else:
            id = self.Daten_Tabelle.item(index, 0).text()
        file = f".\Resources\Images\ID{id}.png"

        dir_ = QFileDialog.getOpenFileName(self, 'Open file', "C:")
        print(dir_)
        if dir_[0] != '':
            shutil.copy2(dir_[0], file)
            print(f"Pixmap zu {file} gesetzt!")
            self.lbl_portrait.setPixmap(QPixmap(file))
            self.path = file
        else:
            print("264 | Upload abgebrochen")

    def photo(self):
        width, height = 1280, 720
        win_name = "cv2 | TakeImage"

        index = self.Daten_Tabelle.currentRow()
        if self.Daten_Tabelle.rowCount() < 1:
            id = 1
        else:
            id = self.Daten_Tabelle.item(index, 0).text()

        file = f".\Resources\Images\ID{id}.png"
        cam = cv2.VideoCapture(0)  # 1280x720 px
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        moved = False
        while True:
            ret, frame = cam.read()
            if not ret:
                print("failed to grab frame")
                break
            cv2.rectangle(frame, (0, 0), (width, height), (255, 255, 255), 2)
            cv2.rectangle(frame,
                          (int((width / 2) - 550 / 2), int((height / 2) - 600 / 2)),  # Links oben: x, y
                          (int((width / 2) + 550 / 2), int((height / 2) + 600 / 2)),  # Rechts oben: x, y
                          (255, 255, 255),
                          2)
            cv2.rectangle(frame,
                          (int(((width / 2) - 550 / 2) - 7), int(((height / 2) - 600 / 2) - 7)),
                          (int(((width / 2) + 550 / 2) + 7), int(((height / 2) + 600 / 2) + 7)),
                          (255, 255, 255),
                          3)
            cv2.imshow(win_name, frame)

            cv2.putText(frame, "Leertaste um Foto zu machen.",
                        (int((width / 2) - 250), int((height / 2) - 320)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)

            cv2.putText(frame, "ESC = Fertig",
                        (int(width - 250), int(height - 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1,
                        (0, 0, 0), 2, cv2.LINE_AA)
            cv2.imshow(win_name, frame)

            if not moved:
                cv2.moveWindow(win_name,
                               int((width / 2) - 550 / 2),
                               int(((height / 2) - 600 / 2)))  # zentriere fenster in der mitte des Bilschirms
                moved = True
            k = cv2.waitKey(1)
            if k % 256 == 27:
                # ESC pressed
                print("Schliesse Kamera..")
                break
            elif k % 256 == 32:
                # SPACE pressed
                # komprimiere auf 550x600 px
                frame = frame[
                        int((height / 2) - 600 / 2):int((height / 2) + 600 / 2),
                        int((width / 2) - 550 / 2):int((width / 2) + 550 / 2)
                        ]
                cv2.imwrite(file, frame)
                print(f"Pixmap zu {file} gesetzt!")
                self.lbl_portrait.setPixmap(QPixmap(file))
                self.path = file
        cam.release()
        cv2.destroyAllWindows()

    def aktualisieren(self):
        self.setCursor(Qt.CursorShape(3))  # cursor wird zu einer Sanduhr gesetzt.
        # Siehe https://doc.qt.io/qt-5/qt.html#CursorShape-enum
        DB_verbinden()  # Verbindung zur DB herstellen

        # Befüllung aus DB-Tabelle 'addresses'
        mycursor.execute("SELECT * FROM addresses")
        fetch = mycursor.fetchall()
        self.lbl_ElementsFound.setText(f"Einträge gefunden: {str(len(fetch))}")

        zeile = 0
        for z in fetch:
            for s in range(0, 20):
                self.Daten_Tabelle.setRowCount(zeile + 1)
                fielditem = QTableWidgetItem(str(z[s]))
                self.Daten_Tabelle.setItem(zeile, s, fielditem)
            zeile += 1

        self.Daten_Tabelle.selectRow(0)
        self.Daten_Tabelle.resizeColumnsToContents()
        self.Daten_Tabelle.resizeRowsToContents()

        DB_schliessen()
        print("Alle Adressen werden in Tabelle angezeigt")
        self.setCursor(Qt.CursorShape(0))

    # ----------------------------------------------------------------------------------------------------------------------
    # notwendig um Programm ausführen zu können

    @pyqtSlot()
    def on_pb_export_clicked(self):
        if self.GESCHLECHT.currentText() == "Männlich":
            anrede = "Herr"
        elif self.GESCHLECHT.currentText() == "Weiblich":
            anrede = "Frau"
        else:
            anrede = ""

        canvas = reportlab.pdfgen.canvas.Canvas("export.pdf")
        canvas.setLineWidth(2)
        canvas.setPageSize((550, 200))

        canvas.setFont('Helvetica', 20)
        canvas.drawString(10, 170, f"{anrede} {self.TITEL1.currentText()} {self.TITEL2.currentText()} "
                                   f"{self.TITEL3.currentText()} {self.FAM_NAME.text()} {self.VOR_NAMEN.text()}")
        canvas.line(8, 164, 400 - 38, 164)

        canvas.setFont('Helvetica', 12)

        canvas.drawString(20, 140, f"Wohnsitz:")
        canvas.drawString(30, 140 - 15 * 1, f"{self.STR.text()} {self.STR_NR.text()}")
        canvas.drawString(30, 140 - 15 * 2, f"{self.PLZ.text()}, {self.ORT.text()}")
        canvas.drawString(30, 140 - 15 * 3, f"{self.LAND.currentText()}")

        canvas.drawString(20, 140 - 15 * 5, "Kontakt Daten:")
        canvas.drawString(30, 140 - 15 * 6, f"Tel. Nr.: {self.MOBIL_VOR.text()} {self.MOBIL_NR.text()}")

        canvas.drawInlineImage(self.path, 400, 30, 550 / 4, 600 / 4)

        canvas.save()
        os.startfile("export.pdf")


app = QApplication(sys.argv)
ui = Main()  # Name der bei der Anlage der Dialog-Klasse verwendet wurde
ui.show()
sys.exit(app.exec())
