from pathlib import Path
from datetime import date
from zipfile import ZipFile, ZIP_DEFLATED
from xml.sax.saxutils import escape
import textwrap

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"
OUT.mkdir(exist_ok=True)

services = {
    "event-ingestor": ROOT / "applications/event-ingestor/app.py",
    "event-processor": ROOT / "applications/event-processor/main.py",
    "event-query-api": ROOT / "applications/event-query-api/main.py",
    "notification-service": ROOT / "applications/notification-service/main.py",
    "dashboard": ROOT / "applications/dashboard/app.py",
}

def read(path):
    return path.read_text(encoding="utf-8")

def xml_text(text, style=None):
    style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ''
    runs = ''.join(
        f'<w:r><w:t xml:space="preserve">{escape(line)}</w:t></w:r>'
        if index == 0 else
        f'<w:r><w:br/><w:t xml:space="preserve">{escape(line)}</w:t></w:r>'
        for index, line in enumerate(text.splitlines() or [''])
    )
    return f'<w:p>{style_xml}{runs}</w:p>'

def code_paragraph(line):
    return '<w:p><w:pPr><w:pStyle w:val="Code"/></w:pPr><w:r><w:t xml:space="preserve">' + escape(line or " ") + '</w:t></w:r></w:p>'

def build_docx(path, sections):
    body = []
    for kind, value in sections:
        if kind == "title": body.append(xml_text(value, "Title"))
        elif kind == "h1": body.append(xml_text(value, "Heading1"))
        elif kind == "h2": body.append(xml_text(value, "Heading2"))
        elif kind == "p": body.append(xml_text(value))
        elif kind == "code": body.extend(code_paragraph(line) for line in value.splitlines())
        elif kind == "bullet": body.append('<w:p><w:pPr><w:pStyle w:val="ListBullet"/></w:pPr><w:r><w:t>' + escape(value) + '</w:t></w:r></w:p>')
    body_xml = ''.join(body) + '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="900" w:right="900" w:bottom="900" w:left="900"/></w:sectPr>'
    document = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{body_xml}</w:body></w:document>'''
    styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:style w:type="paragraph" w:styleId="Normal"><w:name w:val="Normal"/><w:rPr><w:fonts w:ascii="Aptos" w:hAnsi="Aptos"/><w:sz w:val="21"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:rPr><w:b/><w:sz w:val="36"/><w:color w:val="17365D"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="Heading 1"/><w:rPr><w:b/><w:sz w:val="28"/><w:color w:val="1F4E79"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="Heading 2"/><w:rPr><w:b/><w:sz w:val="24"/><w:color w:val="2F75B5"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Code"><w:name w:val="Code"/><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="16"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="ListBullet"><w:name w:val="List Bullet"/></w:style></w:styles>'''
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'''
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'''
    word_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'''
    settings = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:zoom w:percent="100"/></w:settings>'''
    app = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Event Monitoring Documentation Generator</Application></Properties>'''
    with ZipFile(path, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)
        z.writestr("word/styles.xml", styles)
        z.writestr("word/settings.xml", settings)
        z.writestr("docProps/app.xml", app)
        z.writestr("word/_rels/document.xml.rels", word_rels)

def pdf_escape(text): return text.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
def build_pdf(path, lines):
    page_lines = []
    current = []
    for line in lines:
        chunks = textwrap.wrap(line, width=92) or [""]
        for chunk in chunks:
            if len(current) >= 52: page_lines.append(current); current=[]
            current.append(chunk)
    if current: page_lines.append(current)
    # Keep object numbering stable: catalog=1, pages=2, font=3, then page/content pairs.
    objects = [
        '<< /Type /Catalog /Pages 2 0 R >>',
        '<< /Type /Pages /Kids [' + ' '.join(f'{4+i*2} 0 R' for i in range(len(page_lines))) + f'] /Count {len(page_lines)} >>',
        '<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>',
    ]
    for page in page_lines:
        stream = 'BT /F1 9 Tf 45 755 Td 11 TL ' + ' '.join(f'({pdf_escape(x)}) Tj T*' for x in page) + ' ET'
        page_object_number = len(objects) + 1
        content_object_number = page_object_number + 1
        objects += [f'<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 3 0 R >> >> /MediaBox [0 0 612 792] /Contents {content_object_number} 0 R >>', f'<< /Length {len(stream.encode())} >>\nstream\n{stream}\nendstream']
    out=b'%PDF-1.4\n'; offsets=[]
    for n,obj in enumerate(objects,1): offsets.append(len(out)); out += f'{n} 0 obj\n{obj}\nendobj\n'.encode()
    xref=len(out); out += f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode(); out += ''.join(f'{o:010d} 00000 n \n' for o in offsets).encode(); out += f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode(); path.write_bytes(out)

def make_sections():
    s=[("title","Event Monitoring System\nTechnical Project Documentation"),("p",f"Generated from the repository on {date.today().isoformat()}. This document describes the implemented Kubernetes-focused microservices system, its code, infrastructure, operations, and current validation status."),("h1","1. Executive Summary"),("p","The Event Monitoring System receives application, security, and performance events through a Flask ingestion API. Events are cached in Redis, published durably to RabbitMQ, processed asynchronously by a FastAPI worker, persisted to PostgreSQL, and exposed through a query API and Flask dashboard. High and critical events are routed to a notification worker. Prometheus metrics support operational monitoring and Grafana visualization."),("h1","2. Architecture"),("p","The runtime flow is: client or test script -> event-ingestor -> RabbitMQ event_queue -> event-processor -> PostgreSQL processed_events. The processor also writes a short-lived Redis record and publishes high-severity events to notification_queue. The dashboard calls event-query-api, which reads PostgreSQL. Kubernetes supplies service discovery, health probes, resource limits, and workload orchestration."),("h2","Core components"),("bullet","event-ingestor: Flask POST /api/events endpoint, validation, Redis cache, RabbitMQ publication, metrics, and critical-event persistence."),("bullet","event-processor: FastAPI health/metrics surface and a background RabbitMQ consumer with event-specific processing rules."),("bullet","event-query-api: FastAPI read API for recent processed events and severity/status statistics."),("bullet","notification-service: RabbitMQ worker that simulates notifications for high-severity events and exposes Prometheus metrics on port 9000."),("bullet","dashboard: Flask HTML dashboard refreshed every ten seconds through the query API."),("bullet","PostgreSQL, RabbitMQ, Redis: stateful and messaging dependencies deployed in Kubernetes."),("h1","3. Event Contract"),("p","A valid event must contain event_type, source, and severity. message is optional, while metrics and metadata may carry structured values. The ingestor adds timestamp, ingestion_time, and status=pending. The processor adds processed_at and status=processed, or records an error and reports failure."),("code",'''POST /api/events\nContent-Type: application/json\n\n{\n  "event_type": "security_alert",\n  "source": "auth-service",\n  "severity": "critical",\n  "message": "Multiple failed login attempts",\n  "metadata": {"attempts": 12}\n}'''),("h1","4. Service APIs"),("h2","event-ingestor"),("bullet","GET /health returns service health."),("bullet","GET /metrics returns Prometheus exposition data."),("bullet","POST /api/events validates and accepts an event, returning HTTP 202."),("h2","event-query-api"),("bullet","GET /health returns service health."),("bullet","GET /events?limit=25 returns the newest processed events; limit is clamped to 1..100."),("bullet","GET /events/stats returns grouped severity and status counts."),("bullet","GET /metrics returns Prometheus exposition data."),("h2","event-processor"),("bullet","GET /health and GET /metrics provide probe and monitoring surfaces."),("h2","dashboard"),("bullet","GET /health returns service health."),("bullet","GET / renders severity cards and recent processed events."),("h1","5. Processing Rules"),("bullet","security_alert events with critical or high severity generate notification messages."),("bullet","performance_metric events with cpu_percent above 90 receive alert=High CPU Usage."),("bullet","application_log messages containing ERROR or Exception receive needs_attention=true."),("bullet","Successful queue messages are acknowledged. Processing failures are now negatively acknowledged and requeued, preventing silent loss."),("h1","6. Persistence and Data Model"),("p","The database initialization Job creates events and processed_events tables. events stores critical/high events accepted synchronously by the ingestor. processed_events stores the processor output used by the query API and dashboard. JSONB metadata preserves the full event payload and derived fields. Timestamp and severity/status indexes support the primary access patterns."),("h1","7. Kubernetes Deployment"),("p","The manifests define the event-monitoring namespace, Deployments for application workers, StatefulSets for PostgreSQL/RabbitMQ/Redis, Services for internal discovery and selected NodePort access, ConfigMaps, Secrets, probes, resource requests/limits, Ingress, and a database initialization Job. The setup flow builds and pushes images, updates image registry references, applies the namespace and workloads, waits for readiness, and supports port-forwarding for local access."),("code",'''kubectl get pods -n event-monitoring\nkubectl port-forward -n event-monitoring svc/event-ingestor-service 8081:80\nbash scripts/test-events.sh\nkubectl port-forward -n event-monitoring svc/dashboard-service 8080:80'''),("h1","8. Terraform AWS Production Direction"),("p","The Terraform area models a production-oriented AWS path with VPC, EKS, RDS PostgreSQL, and Redis modules. This is distinct from the local Kubernetes manifests: the manifests run the playground stack, while Terraform provisions cloud infrastructure intended to host or support a production deployment. Review variables, credentials, state management, networking, and secret handling before applying to an AWS account."),("h1","9. CI/CD and Observability"),("p","The Jenkins pipeline builds service images, pushes them to a registry, deploys Kubernetes resources, and includes operational stages for verification and rollback. Prometheus configuration scrapes application metrics, while Grafana dashboard JSON provides visualization. Metric families include events_received_total, events_processed_total, and notifications_sent_total."),("h1","10. Security and Reliability Notes"),("bullet","Default credentials exist in application fallbacks and development manifests; production deployments must use managed secrets and rotate credentials."),("bullet","Database connections are opened per operation; production hardening should add pooling, timeouts, and retry/backoff policies."),("bullet","Queue messages are durable and consumers use prefetch_count=1. Requeue behavior protects against transient processing failures, but a dead-letter strategy should be added for poison messages."),("bullet","The dashboard uses server-side template rendering and escapes values through Jinja; production deployments should add authentication, TLS, and access controls."),("bullet","Automated unit/integration tests are not present in the repository. The current verified check is Python compilation; full readiness still requires container, Kubernetes, database, queue, and end-to-end smoke testing."),("h1","11. Source Code Appendix"),("p","The following appendix includes the implemented application source files. Infrastructure manifests, Terraform modules, Dockerfiles, requirements files, and shell scripts remain in their repository paths and are listed in the project inventory." )]
    for name,path in services.items(): s += [("h2",f"Appendix: {name} ({path.relative_to(ROOT).as_posix()})"),("code",read(path))]
    return s

sections=make_sections()
build_docx(OUT/"event-monitoring-system-project-documentation.docx", sections)
plain=[]
for kind,value in sections:
    if kind in ("title","h1","h2"): plain += ["",value.upper()]
    elif kind in ("p","bullet"): plain += [("- " if kind=="bullet" else "")+value]
    elif kind=="code": plain += ["",value]
build_pdf(OUT/"event-monitoring-system-project-documentation.pdf", plain)
print("created", OUT/"event-monitoring-system-project-documentation.docx")
print("created", OUT/"event-monitoring-system-project-documentation.pdf")
