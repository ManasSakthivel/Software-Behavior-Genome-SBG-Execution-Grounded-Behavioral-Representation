       IDENTIFICATION DIVISION.
       PROGRAM-ID. REC.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-N PIC 9 VALUE 0.
       PROCEDURE DIVISION.
       MAIN-PARA.
           PERFORM A-PARA
           STOP RUN.
       A-PARA.
           ADD 1 TO WS-N
           IF WS-N < 3
              PERFORM A-PARA
           END-IF
           DISPLAY "A done N=" WS-N.
