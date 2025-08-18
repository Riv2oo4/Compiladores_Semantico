function suma(a: integer, b: integer): integer { return a + b; }
            let r1: integer = suma(3);         // aridad inválida
            let r2: integer = suma(3, true);   // tipo inválido

            class Calc {
              function sum(a: integer, b: integer): integer { return a + b; }
            }
            let c: Calc = new Calc();
            // let r3: integer = c.sum(2, true);   // descomenta si ya soportas métodos: debe fallar
