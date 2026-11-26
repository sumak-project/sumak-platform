plugins {
    base
    id("sumak.java-conventions") apply false
}

allprojects {
    group = "ec.gob.sumak"
    version = "0.1.0-SNAPSHOT"
}

subprojects {
    apply(plugin = "sumak.java-conventions")
}
