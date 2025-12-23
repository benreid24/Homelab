import process from 'process';

const DOMAIN = process.env.DOMAIN;
const CLOUDFLARE_ZONE_ID = process.env.CLOUDFLARE_ZONE_ID;
const CLOUDFLARE_API_TOKEN = process.env.CLOUDFLARE_API_TOKEN;

interface DnsRecord {
    id: string;
    name: string;
    ttl: number;
    type: string;
    content: string;
}

async function readRecords(zoneId: string): Promise<DnsRecord[]> {
  const response = await fetch(`https://api.cloudflare.com/client/v4/zones/${zoneId}/dns_records`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${CLOUDFLARE_API_TOKEN}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch DNS records: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  return data.result as DnsRecord[];
}

async function getCurrentIp(): Promise<string> {
    const response = await fetch('https://httpbin.org/ip');
    if (!response.ok) {
        throw new Error(`Failed to fetch current IP: ${response.status} ${response.statusText}`);
    }
    const data = await response.json();
    return data.origin;
}

async function createDnsRecord(zoneId: string, record: Omit<DnsRecord, 'id'>): Promise<void> {
    const response = await fetch(`https://api.cloudflare.com/client/v4/zones/${zoneId}/dns_records`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${CLOUDFLARE_API_TOKEN}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(record)
    });
    
    if (!response.ok) {
        throw new Error(`Failed to create DNS record: ${response.status} ${response.statusText}`);
    }
    await response.json();
}

async function updateDnsRecord(zoneId: string, recordId: string, record: Omit<DnsRecord, 'id'>): Promise<void> {
    const response = await fetch(`https://api.cloudflare.com/client/v4/zones/${zoneId}/dns_records/${recordId}`, {
        method: 'PATCH',
        headers: {
            'Authorization': `Bearer ${CLOUDFLARE_API_TOKEN}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(record)
    });

    if (!response.ok) {
        throw new Error(`Failed to update DNS record: ${response.status} ${response.statusText}`);
    }
    await response.json();
}

async function main() {
    if (!DOMAIN) {
        throw new Error('DOMAIN must be set in environment variables.');
    }
    if (!CLOUDFLARE_ZONE_ID || !CLOUDFLARE_API_TOKEN) {
        throw new Error('CLOUDFLARE_ZONE_ID and CLOUDFLARE_API_TOKEN must be set in environment variables.');
    }

    console.log(`Managing DNS for domain: ${DOMAIN}`);

    const currentIp = await getCurrentIp();
    const records = await readRecords(CLOUDFLARE_ZONE_ID);
    const existingRecord = records.find(record => record.name === DOMAIN && record.type === 'A');

    if (!existingRecord) {
        console.log(`No existing DNS A record found for ${DOMAIN}. Creating one.`);
        await createDnsRecord(CLOUDFLARE_ZONE_ID, {
            name: DOMAIN,
            type: 'A',
            content: currentIp,
            ttl: 600
        });
        console.log(`Created new DNS A record for ${DOMAIN} with IP ${currentIp}`);
    }
    else {
        if (existingRecord.content !== currentIp) {
            console.log(`DNS A record for ${DOMAIN} exists but IP differs. Updating from ${existingRecord.content} to ${currentIp}.`);
            await updateDnsRecord(CLOUDFLARE_ZONE_ID, existingRecord.id, {
                name: DOMAIN,
                type: 'A',
                content: currentIp,
                ttl: 600
            });
            console.log(`Updated DNS A record for ${DOMAIN} to IP ${currentIp}`);
        }
        else {
            console.log(`DNS A record for ${DOMAIN} is up-to-date with IP ${currentIp}. No action needed.`);
        }
    }
}

main().catch(error => {
    console.error('Error managing DNS records:', error);
    process.exit(1);
});
