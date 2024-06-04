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

    console.log(await moduleA.getDynamicExtensions(pool, "Dynamic erc721"));

    console.log(moduleA.generateDynamicPrimitiveName("Dynamic erc721", 30));
  } catch (err) {
    console.log(err);
  }
}

await main();
