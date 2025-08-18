class Punto {
              let x: integer;
              function setX(v: integer) { this.x = v; }
              function getX(): integer { return this.x; }
            }
            let p: Punto = new Punto();
            p.setX(5);
            let n: integer = p.getX();
