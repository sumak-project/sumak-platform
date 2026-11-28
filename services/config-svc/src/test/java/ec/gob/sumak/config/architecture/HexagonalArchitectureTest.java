package ec.gob.sumak.config.architecture;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;
import static com.tngtech.archunit.library.dependencies.SlicesRuleDefinition.slices;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

/** Fail-closed checks for config-svc's hexagonal skeleton. */
class HexagonalArchitectureTest {

  private static final String ROOT = "ec.gob.sumak.config";
  private static final String DOMAIN = ROOT + ".domain..";
  private static final String APPLICATION = ROOT + ".application..";
  private static final String PORTS = ROOT + ".port..";
  private static final String ADAPTERS = ROOT + ".adapter..";

  private static JavaClasses classes;

  @BeforeAll
  static void importClasses() {
    classes =
        new ClassFileImporter()
            .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS)
            .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_JARS)
            .importPackages(ROOT);
  }

  @Test
  void domainDoesNotDependOnFrameworkPersistenceOrAdapters() {
    noClasses()
        .that()
        .resideInAPackage(DOMAIN)
        .should()
        .dependOnClassesThat()
        .resideInAnyPackage(
            "org.springframework..",
            "jakarta.persistence..",
            "org.hibernate..",
            "org.apache.kafka..",
            "com.fasterxml.jackson..",
            APPLICATION,
            PORTS,
            ADAPTERS)
        .allowEmptyShould(true)
        .check(classes);
  }

  @Test
  void applicationAndPortsDoNotDependOnAdaptersOrFrameworks() {
    noClasses()
        .that()
        .resideInAnyPackage(APPLICATION, PORTS)
        .should()
        .dependOnClassesThat()
        .resideInAnyPackage(
            ADAPTERS,
            "org.springframework..",
            "jakarta.persistence..",
            "org.hibernate..",
            "org.apache.kafka..")
        .allowEmptyShould(true)
        .check(classes);
  }

  @Test
  void serviceDoesNotImportForeignSumakModules() {
    noClasses()
        .should()
        .dependOnClassesThat()
        .resideInAnyPackage("ec.gob.sumak.identity..", "ec.gob.sumak.gateway..")
        .allowEmptyShould(true)
        .check(classes);
  }

  @Test
  void packageDependencyGraphIsAcyclic() {
    slices()
        .matching(ROOT + ".(*)..")
        .should()
        .beFreeOfCycles()
        .allowEmptyShould(true)
        .check(classes);
  }

  @Test
  void skeletonDeclaresEveryHexagonalPackage() {
    Path sources = Path.of("src", "main", "java", "ec", "gob", "sumak", "config");

    List.of("domain", "application", "port/in", "port/out", "adapter/in", "adapter/out")
        .forEach(
            layer ->
                assertTrue(
                    Files.isRegularFile(sources.resolve(layer).resolve("package-info.java")),
                    () -> "Missing package declaration for " + layer));
  }

  @Test
  void serviceHasNoBusinessRestOrPersistenceImplementation() {
    noClasses()
        .should()
        .dependOnClassesThat()
        .resideInAnyPackage(
            "org.springframework.web..",
            "jakarta.ws.rs..",
            "javax.ws.rs..",
            "jakarta.persistence..",
            "org.hibernate..")
        .check(classes);
  }
}
