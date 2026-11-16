       IDENTIFICATION DIVISION.
       PROGRAM-ID. GT.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-N PIC 9 VALUE 0.
       PROCEDURE DIVISION.
       P1.
           ADD 1 TO WS-N
           IF WS-N < 3 GO TO P1.
       P2.
           DISPLAY "N=" WS-N
           STOP RUN.
