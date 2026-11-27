package ec.gob.sumak.gateway;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.reactive.server.WebTestClient.bindToApplicationContext;

import ec.gob.sumak.gateway.management.VersionEndpoint;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.ApplicationContext;
import org.springframework.test.web.reactive.server.WebTestClient;

@SpringBootTest(properties = "spring.application.version=contract-test")
class GatewayManagementContractTest {

    @Autowired
    ApplicationContext context;

    @Test
    void publishesTechnicalHealthAndVersionEndpointsOnly() {
        WebTestClient client = bindToApplicationContext(context).build();

        client.get().uri("/health").exchange().expectStatus().isOk();
        client.get().uri("/health/live").exchange().expectStatus().isOk();
        client.get().uri("/health/ready").exchange().expectStatus().isOk();
        client.get().uri("/health/startup").exchange().expectStatus().isOk();
        client.get().uri("/version")
                .exchange()
                .expectStatus().isOk()
                .expectBody()
                .jsonPath("$.application").isEqualTo("api-gateway")
                .jsonPath("$.version").isEqualTo("contract-test");
        client.get().uri("/business").exchange().expectStatus().isUnauthorized();
    }

    @Test
    void versionEndpointIsTheConfiguredActuatorEndpoint() {
        assertThat(context.getBean(VersionEndpoint.class)).isNotNull();
    }
}
