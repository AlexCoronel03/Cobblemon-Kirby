plugins {
    id("fabric-loom") version "1.17.16"
    `java`
}

version = project.property("mod_version") as String
group = project.property("maven_group") as String

base {
    archivesName.set(project.property("archives_base_name") as String)
}

repositories {
    // Cobblemon is published through Modrinth's Maven proxy (maven.modrinth:<slug>:<version id>).
    maven("https://api.modrinth.com/maven") {
        name = "Modrinth"
        content { includeGroup("maven.modrinth") }
    }
    mavenCentral()
}

dependencies {
    minecraft("com.mojang:minecraft:${project.property("minecraft_version")}")
    mappings(loom.officialMojangMappings())
    modImplementation("net.fabricmc:fabric-loader:${project.property("loader_version")}")
    modImplementation("net.fabricmc.fabric-api:fabric-api:${project.property("fabric_version")}")

    // Cobblemon 1.8.1 (Fabric, MC 1.21.1). Not shaded: players install Cobblemon themselves.
    modImplementation("maven.modrinth:cobblemon:${project.property("cobblemon_version")}")

    // Cobblemon's API is written in Kotlin; the Kotlin stdlib types that appear in its signatures come from
    // Fabric Language Kotlin, which Cobblemon already bundles at runtime. Compile-time only here.
    modCompileOnly("net.fabricmc:fabric-language-kotlin:${project.property("kotlin_loader_version")}")

    testImplementation("org.junit.jupiter:junit-jupiter:5.10.2")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
    withSourcesJar()
}

tasks.withType<JavaCompile>().configureEach {
    options.encoding = "UTF-8"
    options.release.set(21)
}

tasks.processResources {
    inputs.property("version", project.version)
    filesMatching("fabric.mod.json") {
        expand(mapOf("version" to project.version))
    }
}

tasks.test {
    useJUnitPlatform()
}
