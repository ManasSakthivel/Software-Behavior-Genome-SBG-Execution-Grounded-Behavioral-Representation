       IDENTIFICATION DIVISION.
       PROGRAM-ID. COL.
       PROCEDURE DIVISION.
           IF "a" < "A"
              DISPLAY "a<A (EBCDIC order)"
           ELSE
              DISPLAY "a>A (ASCII order)"
           END-IF
           IF "1" < "A"
              DISPLAY "1<A"
           ELSE
              DISPLAY "1>A (EBCDIC: digits after letters)"
           END-IF
           STOP RUN.
