# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'src/gui/main_window_aisimogen.ui'
#
# Created by: PyQt5 UI code generator 5.15.10
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(640, 480)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.pushButton_generate_response = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_generate_response.setGeometry(QtCore.QRect(550, 140, 75, 23))
        self.pushButton_generate_response.setObjectName("pushButton_generate_response")
        self.plainTextEdit_prompt = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.plainTextEdit_prompt.setGeometry(QtCore.QRect(20, 30, 601, 101))
        self.plainTextEdit_prompt.setObjectName("plainTextEdit_prompt")
        self.plainTextEdit_response = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.plainTextEdit_response.setGeometry(QtCore.QRect(20, 220, 601, 201))
        self.plainTextEdit_response.setReadOnly(True)
        self.plainTextEdit_response.setObjectName("plainTextEdit_response")
        self.label_prompt = QtWidgets.QLabel(self.centralwidget)
        self.label_prompt.setGeometry(QtCore.QRect(20, 10, 47, 13))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_prompt.setFont(font)
        self.label_prompt.setObjectName("label_prompt")
        self.label_response = QtWidgets.QLabel(self.centralwidget)
        self.label_response.setGeometry(QtCore.QRect(20, 200, 71, 16))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_response.setFont(font)
        self.label_response.setObjectName("label_response")
        self.progressBar_request_prompt = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar_request_prompt.setGeometry(QtCore.QRect(20, 140, 171, 21))
        self.progressBar_request_prompt.setProperty("value", 0)
        self.progressBar_request_prompt.setObjectName("progressBar_request_prompt")
        self.label_progress_request_prompt = QtWidgets.QLabel(self.centralwidget)
        self.label_progress_request_prompt.setGeometry(QtCore.QRect(210, 140, 91, 21))
        self.label_progress_request_prompt.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_progress_request_prompt.setObjectName("label_progress_request_prompt")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 640, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "AISiMoGen - AI Simscape Model Generator v.0.1"))
        self.pushButton_generate_response.setText(_translate("MainWindow", "Send"))
        self.label_prompt.setText(_translate("MainWindow", "Prompt"))
        self.label_response.setText(_translate("MainWindow", "Response"))
        self.label_progress_request_prompt.setText(_translate("MainWindow", "Press button..."))
