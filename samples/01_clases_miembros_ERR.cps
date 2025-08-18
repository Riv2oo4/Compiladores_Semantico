class Punto { let x: integer; }
            let p: Punto = new Punto();
            let y: integer = p.y;     // no existe y (o tipo incompatible)
            // p.setX("hola");        // si ya soportas métodos, descomenta y también debe fallar
