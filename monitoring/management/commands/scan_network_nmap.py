from django.core.management.base import BaseCommand
from monitoring.scanner.nmap_scanner import scan_network


class Command(BaseCommand):
    help = "Scan network using nmap and update devices."

    def add_arguments(self, parser):
        parser.add_argument(
            "--range",
            required=True,
            help="Network range to scan (e.g. 192.168.56.0/24)"
        )
        parser.add_argument(
            "--sudo",
            action="store_true",
            help="Run nmap with sudo"
        )

    def handle(self, *args, **options):
        result = scan_network(
            network_range=options["range"],
            use_sudo=options["sudo"],
            triggered_by="manual"
        )

        self.stdout.write(
            self.style.SUCCESS(f"✅ Scan complete: {result}")
        )
