let x: integer = 1;
            { let x: integer = 2; }          // shadow válido
            function f(a: integer): integer {
                { let a: integer = 5; }      // parámetro sombreado en bloque: permitido si tu semántica lo permite
                return a;
            }
            let r: integer = f(2);
