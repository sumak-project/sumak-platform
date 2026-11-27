package ec.gob.sumak.gateway.architecture;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.classes;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;

import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.junit.AnalyzeClasses;
import com.tngtech.archunit.junit.ArchTest;
import com.tngtech.archunit.lang.ArchRule;
import org.springframework.boot.actuate.endpoint.annotation.Endpoint;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RestController;

@AnalyzeClasses(
        packages = "ec.gob.sumak.gateway",
        importOptions = ImportOption.DoNotIncludeTests.class)
class GatewayArchitectureTest {

    @ArchTest
    static final ArchRule gatewayDoesNotOwnPersistenceOrRepositories =
            noClasses()
                    .that().resideInAPackage("ec.gob.sumak.gateway..")
                    .should().dependOnClassesThat()
                    .resideInAnyPackage("..persistence..", "..repository..", "jakarta.persistence..");

    @ArchTest
    static final ArchRule gatewayHasNoBusinessRestControllers =
            noClasses()
                    .that().resideInAPackage("ec.gob.sumak.gateway..")
                    .should().beAnnotatedWith(RestController.class)
                    .orShould().beAnnotatedWith(Controller.class);

    @ArchTest
    static final ArchRule technicalManagementEndpointsAreOutsideBootstrapAndConfiguration =
            classes()
                    .that().areAnnotatedWith(Endpoint.class)
                    .should().resideInAPackage("ec.gob.sumak.gateway.management..")
                    .andShould().resideOutsideOfPackage("ec.gob.sumak.gateway.config..")
                    .andShould().resideOutsideOfPackage("ec.gob.sumak.gateway");
}
