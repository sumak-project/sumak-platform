package ec.gob.sumak.gateway.management;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class GatewayManagementEndpointTest {

    @Test
    void exposesOnlyApplicationAndConfiguredVersion() {
        var endpoint = new VersionEndpoint("api-gateway", "1.2.3");

        assertThat(endpoint.version())
                .containsOnlyKeys("application", "version")
                .containsEntry("application", "api-gateway")
                .containsEntry("version", "1.2.3");
    }
}
