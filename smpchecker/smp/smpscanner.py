import logging
import requests
import csv
import xml.etree.ElementTree as Et
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from smpchecker.sml import smlchecker
from smpchecker.model import model
from smpchecker.smp import smpscanner


log = logging.getLogger(__name__)

ns = {'pub': 'http://busdox.org/serviceMetadata/publishing/1.0/',
      'id': 'http://busdox.org/transport/identifiers/1.0/',
      'addr': 'http://www.w3.org/2005/08/addressing'}

begin_certificate = "-----BEGIN CERTIFICATE-----\n"
end_certificate = "\n-----END CERTIFICATE-----"

def scan(peppolid):
    '''

    Scans an smp for a specific PEPPOL identifier. Assumes that the peppol member is registred in SML

    :param peppolid: PEPPOL identifier
    :return:
    '''

    log.info('Scanning peppolid='+peppolid)

    p = model.PeppolMember(peppolid)
    if p.exists() is False:
        p.create()
    else:
        p.load(peppolid)
        p.update()

    ir = requests.get("http://"+smlchecker.hostname(p.peppolidentifier)+"/iso6523-actorid-upis::"+p.peppolidentifier)

    log.debug(' ----- ServiceGroup for: %s -----', peppolid)
    log.debug(ir.text)
    log.debug(' -------------------------------------------')

    root = Et.fromstring(ir.text)
    collection = root.findall('pub:ServiceMetadataReferenceCollection', ns)

    # size should be 1
    if len(collection) != 1:
        log.error("ServiceGroup XML ServiceMetadataReferenceCollection > 1 p.peppolidentifier=", p.peppolidentifier)

    smrs = collection[0].findall("pub:ServiceMetadataReference", ns)

    for smr in smrs:
        log.debug('smr=%s', smr)
        href = smr.attrib['href']
        if href.startswith("http://") or href.startswith("https://"):
            url = href
        else :
            url= 'http://' + href

        scan_servicemetadata(url, p)


def scan_servicemetadata(url, member):
    '''

    Scans an URL for the SMP metadata

    :param url:
    :return:
    '''
    ir = requests.get(url)

    log.debug(' ------------- ServiceMetada ---------------', url)
    log.debug(' -- for : %s', url)
    log.debug(ir.text)
    log.debug(' -------------------------------------------')

    root = Et.fromstring(ir.text)
    for elem in root.iter('{http://busdox.org/serviceMetadata/publishing/1.0/}SignedServiceMetadata'):
        documenttype = elem.findall('./pub:ServiceMetadata/pub:ServiceInformation/id:DocumentIdentifier', ns)[0].text
        entry = model.SMPEntry(documenttype, member.id)
        processes = elem.findall('./pub:ServiceMetadata/pub:ServiceInformation/pub:ProcessList/pub:Process', ns)
        for p in processes:
            addresses = p.findall('./pub:ServiceEndpointList/pub:Endpoint/addr:EndpointReference/addr:Address', ns)
            #TODO should be only one. build check for it
            for address in addresses:
               entry.endpointurl = address.text

            # Holds the complete signing certificate of the recipient AP, as a PEM base 64 encoded X509 DER
            # formatted value. Check with openssl: 1) add begin and end certificate lines
            # 2) openssl x509  -in test-begin-end.bin -inform pem -text
            certificate = p.findall('./pub:ServiceEndpointList/pub:Endpoint/pub:Certificate', ns)[0]

            c = begin_certificate + certificate.text + end_certificate
            cert = x509.load_pem_x509_certificate(c.encode(), default_backend())
            entry.certificate_not_after = cert.not_valid_before
            entry.certificate_not_before = cert.not_valid_after
            #for s in cert.subject:
             #   print(s.oid)
                #if s.oid.name = 'commonName':
                #    print(s.value)

            if entry.exists() is False:
                entry.create()
            else:
                entry.load(documenttype, member.id)
                entry.update()


def readfile(filename, businessidentifier):
    log.debug('Opening file:'+filename)
    with open(filename) as csvfile:
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        reader = csv.reader(csvfile, dialect)
        results=[]
        for row in reader:
            if businessidentifier == 'PEPPOL':
                peppolid = row[0]
            else:
                peppolid = businessidentifier + ':' + row[0]

            if smlchecker.check(peppolid):
                smpscanner.scan(peppolid)
                p = model.PeppolMember(peppolid)
                p.reload()
                result = p.get_scan_result()
                results.append(result)
            else:
                # create a dummy result; not found
                p = model.PeppolMember(row[0])
                result = model.SMPScanResult(p,[])
                results.append(result)

        return results
