import { EconolensClient } from '../dist/index.js';

const client = new EconolensClient({
  baseUrl: process.env.MCP_BASE_URL || 'https://mechafil-mcp-server.fly.dev/mcp',
  tokenProvider: async () => null,
});

async function main() {
  const ctx = await client.fetchContext();
  console.log('Context length:', ctx.length);

  const hist = await client.getHistoricalData({ fields: ['raw_byte_power'] });
  console.log('Hist keys:', Object.keys(hist || {}));

  const sim = await client.simulate({ forecast_length_days: 90, requested_metric: 'available_supply' });
  console.log('Sim keys:', Object.keys(sim || {}));

  const plot = await client.providePlot({
    series: 'historical_raw_power_eib',
    start_date_key: 'data_start_date',
    title: 'Network Power',
  });
  console.log('Plot response type:', typeof plot);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
