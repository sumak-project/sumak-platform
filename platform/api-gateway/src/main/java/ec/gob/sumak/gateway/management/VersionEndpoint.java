package ec.gob.sumak.gateway.management;

import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.actuate.endpoint.annotation.Endpoint;
import org.springframework.boot.actuate.endpoint.annotation.ReadOperation;
import org.springframework.stereotype.Component;

@Component
@Endpoint(id = "version")
public class VersionEndpoint {

    private final String application;
    private final String version;

    public VersionEndpoint(
            @Value("${spring.application.name}") String application,
            @Value("${spring.application.version:unknown}") String version) {
        this.application = application;
        this.version = version;
    }

    @ReadOperation
    public Map<String, String> version() {
        return Map.of("application", application, "version", version);
    }
}
