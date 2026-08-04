import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class AntivirusError(Exception):
    pass


class VirusFoundError(AntivirusError):
    pass


def scan_bytes(file_bytes: bytes, filename: str = "") -> None:
    """
    Scan file bytes with ClamAV.
    Raises VirusFoundError if a threat is detected.
    Raises AntivirusError on connection/scan failure.
    Does nothing if CLAMAV_ENABLED is False (dev mode).
    """
    if not getattr(settings, "CLAMAV_ENABLED", False):
        logger.debug("clamav_skipped", extra={"filename": filename})
        return

    try:
        import clamd
        cd = clamd.ClamdNetworkSocket(
            host=settings.CLAMAV_HOST,
            port=settings.CLAMAV_PORT,
            timeout=30,
        )
        result = cd.instream(iter([file_bytes]))
        # result is {'stream': ('OK', None)} or {'stream': ('FOUND', 'Eicar-Test-Signature')}
        stream_result = result.get("stream", ("OK", None))
        status, virus_name = stream_result

        if status == "FOUND":
            logger.warning("virus_found", extra={"filename": filename, "virus": virus_name})
            raise VirusFoundError(f"Threat detected: {virus_name}")

        logger.info("clamav_clean", extra={"filename": filename})

    except VirusFoundError:
        raise
    except Exception as exc:
        logger.error("clamav_error", extra={"error": str(exc)})
        # In production, fail closed — reject the file if ClamAV is unreachable
        if not settings.DEBUG:
            raise AntivirusError(f"Antivirus scan failed: {exc}") from exc
        # In dev, log and continue
        logger.warning("clamav_unavailable_continuing_in_dev")
