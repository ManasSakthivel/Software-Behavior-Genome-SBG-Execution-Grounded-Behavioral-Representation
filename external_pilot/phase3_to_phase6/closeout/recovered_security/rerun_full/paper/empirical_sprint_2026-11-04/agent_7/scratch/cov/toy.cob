       IDENTIFICATION DIVISION.
       PROGRAM-ID. TOY.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01  WS-I      PIC 9(2)  VALUE 0.
       01  WS-SUM    PIC 9(3)  VALUE 0.
       01  WS-SMALL  PIC 9(2)  VALUE 0.
       01  WS-NAME   PIC X(6)  VALUE SPACES.
       01  WS-TAB.
           05 WS-ELT PIC 9(2) OCCURS 3 TIMES VALUE 0.
       PROCEDURE DIVISION.
       MAIN-PARA.
           PERFORM LOOP-PARA VARYING WS-I FROM 1 BY 1 UNTIL WS-I > 5
           DISPLAY "SUM=" WS-SUM
           PERFORM OVF-PARA
           CALL "NOSUCHPROG"
               ON EXCEPTION DISPLAY "CALL-EXC"
           END-CALL
           MOVE "ABC" TO WS-NAME
           DISPLAY "NAME=[" WS-NAME "]"
           MOVE 7 TO WS-ELT(2)
           DISPLAY "TAB=" WS-TAB
           MOVE 3 TO RETURN-CODE
           STOP RUN.
       LOOP-PARA.
           COMPUTE WS-SUM = WS-SUM + WS-I * 2.
       OVF-PARA.
           COMPUTE WS-SMALL = WS-SUM * 5
               ON SIZE ERROR DISPLAY "SIZE-ERR"
               NOT ON SIZE ERROR DISPLAY "NO-SIZE-ERR"
           END-COMPUTE.
