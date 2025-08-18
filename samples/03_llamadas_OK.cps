function suma(a: integer, b: integer): integer { return a + b; }
            let r: integer = suma(2, 3);

            class Calc {
              function sum(a: integer, b: integer): integer { return a + b; }
            }
            let c: Calc = new Calc();
            let r2: integer = c.sum(2, 3);     // si aún no soportas métodos, activa SKIP_CLASSES
