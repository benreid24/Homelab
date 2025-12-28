import process from 'process';

interface ManagedDomain {
    domain: string;
    zoneId: string;
}

const DOMAINS = JSON.parse(process.env.DOMAINS || '[]') as ManagedDomain[];
const CLOUDFLARE_API_TOKEN = process.env.CLOUDFLARE_API_TOKEN as string;

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

async function checkAndUpdateDNS(zoneId: string, domain: string, existingRecords: DnsRecord[], currentIp: string): Promise<void> {
    const existingRecord = existingRecords.find(record => record.name === domain && record.type === 'A');

    if (!existingRecord) {
        console.log(`No existing DNS A record found for ${domain}. Creating one.`);
        await createDnsRecord(zoneId, {
            name: domain,
            type: 'A',
            content: currentIp,
            ttl: 600
        });
        console.log(`Created new DNS A record for ${domain} with IP ${currentIp}`);
    }
    else {
        if (existingRecord.content !== currentIp) {
            console.log(`DNS A record for ${domain} exists but IP differs. Updating from ${existingRecord.content} to ${currentIp}.`);
            await updateDnsRecord(zoneId, existingRecord.id, {
                name: domain,
                type: 'A',
                content: currentIp,
                ttl: 600
            });
            console.log(`Updated DNS A record for ${domain} to IP ${currentIp}`);
        }
        else {
            console.log(`DNS A record for ${domain} is up-to-date with IP ${currentIp}. No action needed.`);
        }
    }
}

async function main() {
    if (!DOMAINS.length) {
        throw new Error('DOMAINS must be set in environment variables.');
    }
    if (!CLOUDFLARE_API_TOKEN) {
        throw new Error('CLOUDFLARE_API_TOKEN must be set in environment variables.');
    }

    for (const { domain, zoneId } of DOMAINS) {
        console.log(`Managing DNS for domain: ${domain}`);

        const currentIp = await getCurrentIp();
        const records = await readRecords(zoneId);
        await checkAndUpdateDNS(zoneId, domain, records, currentIp);
        await checkAndUpdateDNS(zoneId, `*.${domain}`, records, currentIp);
    }
}

main().catch(error => {
    console.error('Error managing DNS records:', error);
    process.exit(1);
});
