import pg from "pg";

async function main() {
  try {
    const moduleA = await import("@paima/utils-backend");

    const { Pool } = pg;

    const pool = new Pool({
      host: "localhost",
      port: 5440,
      user: "postgres",
      max: 20,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    });

    const extensions = await moduleA.getDynamicExtensions(
      pool,
      "Dynamic erc721",
    );

    for (const ext of extensions) {
      console.log("name", ext.name);
      console.log("config", JSON.stringify(ext.config, undefined, "\t"));

      console.log(
        "byName",
        await moduleA.getDynamicExtensionByName(pool, ext.name),
      );
    }

    console.log(moduleA.generateDynamicPrimitiveName("Dynamic erc721", 30));
  } catch (err) {
    console.log(err);
  }
}

await main();
