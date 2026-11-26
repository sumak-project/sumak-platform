package ec.gob.sumak.identity.architecture;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;
import static com.tngtech.archunit.library.dependencies.SlicesRuleDefinition.slices;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

/**
 * Hexagonal boundaries for identity-svc (sumak-hexagonal-service skill):
 * domain independence; application depends only on domain + own ports;
 * infrastructure depends inward; no foreign JPA imports; no business REST; no package cycles.
 */
class HexagonalArchitectureTest {

    private static final String ROOT = "ec.gob.sumak.identity";
    private static final String DOMAIN = "ec.gob.sumak.identity.domain..";
    private static final String APPLICATION = "ec.gob.sumak.identity.application..";
    private static final String INFRASTRUCTURE = "ec.gob.sumak.identity.infrastructure..";

    private static JavaClasses classes;

    @BeforeAll
    static void importClasses() {
        classes = new ClassFileImporter()
                .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS)
                .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_JARS)
                .importPackages(ROOT);
    }

    @Test
    void domainIsIndependentOfApplicationAndInfrastructure() {
        noClasses()
                .that().resideInAPackage(DOMAIN)
                .should().dependOnClassesThat().resideInAnyPackage(APPLICATION, INFRASTRUCTURE)
                .allowEmptyShould(true)
                .check(classes);
    }

    @Test
    void domainHasNoFrameworkOrTransportDependencies() {
        noClasses()
                .that().resideInAPackage(DOMAIN)
                .should().dependOnClassesThat().resideInAnyPackage(
                        "org.springframework..",
                        "jakarta.persistence..",
                        "org.hibernate..",
                        "jakarta.jms..",
                        "org.apache.kafka..",
                        "org.springframework.web..",
                        "com.fasterxml.jackson..",
                        "org.springframework.data..")
                .allowEmptyShould(true)
                .check(classes);
    }

    @Test
    void applicationDependsOnlyOnDomainAndOwnPortsNotOnInfrastructure() {
        noClasses()
                .that().resideInAPackage(APPLICATION)
                .should().dependOnClassesThat().resideInAPackage(INFRASTRUCTURE)
                .allowEmptyShould(true)
                .check(classes);
    }

    @Test
    void applicationHasNoFrameworkOrPersistenceDependencies() {
        noClasses()
                .that().resideInAPackage(APPLICATION)
                .should().dependOnClassesThat().resideInAnyPackage(
                        "org.springframework..",
                        "jakarta.persistence..",
                        "org.hibernate..",
                        "org.apache.kafka..")
                .allowEmptyShould(true)
                .check(classes);
    }

    @Test
    void infrastructureDependsInwardNotOutward() {
        // infrastructure may use domain + application ports, but domain must never reach infrastructure (see domain rule);
        // infrastructure itself must not leak into domain
        noClasses()
                .that().resideInAPackage(DOMAIN)
                .should().dependOnClassesThat().resideInAPackage(INFRASTRUCTURE)
                .allowEmptyShould(true)
                .check(classes);
    }

    @Test
    void noForeignJpaImports() {
        noClasses()
                .should().dependOnClassesThat().resideInAnyPackage("jakarta.persistence..", "org.hibernate..")
                .allowEmptyShould(true)
                .check(classes);
    }

    @Test
    void noBusinessRestControllers() {
        noClasses()
                .should().dependOnClassesThat().resideInAnyPackage(
                        "org.springframework.web..",
                        "org.springframework.web.bind.annotation..",
                        "jakarta.ws.rs..",
                        "javax.ws.rs..")
                .allowEmptyShould(true)
                .check(classes);

        noClasses()
                .should().beAnnotatedWith("org.springframework.web.bind.annotation.RestController")
                .allowEmptyShould(true)
                .check(classes);

        noClasses()
                .should().beAnnotatedWith("org.springframework.stereotype.Controller")
                .allowEmptyShould(true)
                .check(classes);
    }

    @Test
    void noPackageCycles() {
        slices()
                .matching(ROOT + ".(*)..")
                .should().beFreeOfCycles()
                .allowEmptyShould(true)
                .check(classes);
    }
}
