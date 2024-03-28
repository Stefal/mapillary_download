#source : https://gitlab.com/geovisio/geo-picture-tag-reader/-/blob/main/geopic_tag_reader/writer.py
from typing import Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from model import PictureType

try:
    import pyexiv2  # type: ignore
except ImportError:
    raise Exception(
        """Impossible to write the exif tags without the '[write-exif]' dependency (that will need to install libexiv2).
Install this package with `pip install geopic-tag-reader[write-exif]` to use this function"""
    )
import timezonefinder  # type: ignore
import pytz


tz_finder = timezonefinder.TimezoneFinder()


@dataclass
class PictureMetadata:
    artist: Optional[str] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    capture_time: Optional[datetime] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    altitude: Optional[float] = None
    picture_type: Optional[PictureType] = None
    direction: Optional[float] = None
    orientation: Optional[int] = 1

class Writer():
    def __init__(self, picture: bytes) -> None:
        self.content = picture
        self.image = pyexiv2.ImageData(picture)
        self.exif = self.image.read_exif()
        self.xmp = self.image.read_xmp()
        self.updated_exif = {}
        self.updated_xmp = {}

    def __enter__(self):
        return self
    
    def __exit__(self, *args) -> None:
        self.image.close()

    def apply(self) -> None:
        try:
            if self.updated_exif:
                self.image.modify_exif(self.updated_exif)
            if self.updated_xmp:
                self.image.modify_xmp(self.updated_xmp)
        except Exception as e:
            print("exception \nexif: {}\nxmp: {}".format(self.updated_exif, self.updated_xmp))

    def close(self) -> None:
        self.image.close()

    def get_Bytes(self) -> bytes:
        return self.image.get_bytes()
    
    def writePictureMetadata(self, metadata: PictureMetadata) -> None:
        """
        Override exif metadata on raw picture and return updated bytes
        """
        if not metadata.capture_time and not metadata.longitude and not metadata.latitude and not metadata.picture_type:
            return

        if metadata.capture_time:
            self.add_gps_datetime(metadata)
            self.add_datetimeoriginal(metadata)

        if metadata.latitude is not None and metadata.longitude is not None:
            self.add_lat_lon(metadata)

        if metadata.picture_type is not None:
            self.add_img_projection(metadata)

    def add_lat_lon(self, metadata: PictureMetadata) -> None:
        """
        Add latitude and longitude values in GPSLatitude + GPSLAtitudeRef and GPSLongitude + GPSLongitudeRef
        """
        if metadata.latitude is not None:
            self.updated_exif["Exif.GPSInfo.GPSLatitudeRef"] = "N" if metadata.latitude > 0 else "S"
            self.updated_exif["Exif.GPSInfo.GPSLatitude"] = self._to_exif_dms(metadata.latitude)

        if metadata.longitude is not None:
            self.updated_exif["Exif.GPSInfo.GPSLongitudeRef"] = "E" if metadata.longitude > 0 else "W"
            self.updated_exif["Exif.GPSInfo.GPSLongitude"] = self._to_exif_dms(metadata.longitude)

    def add_altitude(self, metadata: PictureMetadata, precision: int = 1000) -> None:
        """
        Add altitude value in GPSAltitude and GPSAltitudeRef
        """
        altitude = metadata.altitude

        if altitude is not None:
            negative_altitude = 0 if altitude >= 0 else 1
            self.updated_exif['Exif.GPSInfo.GPSAltitude'] = f"{int(abs(altitude * precision))} / {precision}"
            self.updated_exif['Exif.GPSInfo.GPSAltitudeRef'] = negative_altitude

    def add_direction(self, metadata: PictureMetadata, ref: str = 'T', precision: int = 1000) -> None:
        """
        Add direction value in GPSImgDirection and GPSImgDirectionRef
        """
        direction = metadata.direction

        if metadata.direction is not None:
            self.updated_exif['Exif.GPSInfo.GPSImgDirection'] = f"{int(abs(direction % 360.0 * precision))} / {precision}"
            self.updated_exif['Exif.GPSInfo.GPSImgDirectionRef'] = ref

    def add_gps_datetime(self, metadata: PictureMetadata) -> None:
        """
        Add GPSDateStamp and GPSTimeStamp
        """

        if metadata.capture_time.utcoffset() is None:
            metadata.capture_time = self.localize(metadata.capture_time, metadata)

            # for capture time, override GPSInfo time and DatetimeOriginal
            self.updated_exif["Exif.Photo.DateTimeOriginal"] = metadata.capture_time.strftime("%Y:%m:%d %H:%M:%S")
            offset = metadata.capture_time.utcoffset()
            if offset is not None:
                self.updated_exif["Exif.Photo.OffsetTimeOriginal"] = self.format_offset(offset)

            utc_dt = metadata.capture_time.astimezone(tz=pytz.UTC)
            self.updated_exif["Exif.GPSInfo.GPSDateStamp"] = utc_dt.strftime("%Y:%m:%d")
            self.updated_exif["Exif.GPSInfo.GPSTimeStamp"] = utc_dt.strftime("%H/1 %M/1 %S/1")
        
    def add_datetimeoriginal(self, metadata: PictureMetadata) -> None:
        """
        Add date time in Exif DateTimeOriginal and SubSecTimeOriginal tags
        """

        if metadata.capture_time.utcoffset() is None:
            metadata.capture_time = self.localize(metadata.capture_time, metadata)

            # for capture time, override DatetimeOriginal and SubSecTimeOriginal
            self.updated_exif["Exif.Photo.DateTimeOriginal"] = metadata.capture_time.strftime("%Y:%m:%d %H:%M:%S")
            offset = metadata.capture_time.utcoffset()
            if offset is not None:
                self.updated_exif["Exif.Photo.OffsetTimeOriginal"] = self.format_offset(offset)
            if metadata.capture_time.microsecond != 0:
                self.updated_exif["Exif.Photo.SubSecTimeOriginal"] = metadata.capture_time.strftime("%f")

    def add_img_projection(self, metadata: PictureMetadata) -> None:
        """
        Add image projection type (equirectangular for spherical image, ...) in xmp GPano.ProjectionType
        """

        if metadata.picture_type.value != "flat":
            self.updated_xmp["Xmp.GPano.ProjectionType"] = metadata.picture_type.value
            self.updated_xmp["Xmp.GPano.UsePanoramaViewer"] = True

    def add_artist(self, metadata: PictureMetadata) -> None:
        """
        Add image author in Exif Artist tag
        """

        if metadata.artist is not None:
            self.updated_exif["Exif.Image.Artist"] = ascii(metadata.artist).strip("'")


    def add_camera_make(self, metadata: PictureMetadata) -> None:
        """
        Add camera manufacture in Exif Make tag
        """

        if metadata.camera_make is not None:
            self.updated_exif["Exif.Image.Make"] = ascii(metadata.camera_make).strip("'")


    def add_camera_model(self, metadata: PictureMetadata) -> None:
        """
        Add camera model in Exif Model tag
        """

        if metadata.camera_model is not None:
            self.updated_exif["Exif.Image.Model"] = ascii(metadata.camera_model).strip("'")

    def format_offset(self, offset: timedelta) -> str:
        """Format offset for OffsetTimeOriginal. Format is like "+02:00" for paris offset
        >>> format_offset(timedelta(hours=5, minutes=45))
        '+05:45'
        >>> format_offset(timedelta(hours=-3))
        '-03:00'
        """
        offset_hour, remainer = divmod(offset.total_seconds(), 3600)
        return f"{'+' if offset_hour >= 0 else '-'}{int(abs(offset_hour)):02}:{int(remainer/60):02}"

    def localize(self, naive_dt: datetime, metadata: PictureMetadata) -> datetime:
        """
        Localize a datetime in the timezone of the picture
        If the picture does not contains GPS position, the datetime will not be modified.
        """

        new_lat_lon = metadata.longitude is not None and metadata.latitude is not None
        if new_lat_lon :
            lon = metadata.longitude
            lat = metadata.latitude

        else:
            exif = self.exif
            try:
                lon = exif["Exif.GPSInfo.GPSLongitude"]
                lon_ref = exif.get("Exif.GPSInfo.GPSLongitudeRef", "E")
                lat = exif["Exif.GPSInfo.GPSLatitude"]
                lat_ref = exif.get("Exif.GPSInfo.GPSLatitudeRef", "N")
                lon = self._from_dms(lon) * (1 if lon_ref == "E" else -1)
                lat = self._from_dms(lat) * (1 if lat_ref == "N" else -1)
            except KeyError:
                return metadata.capture_time # canot localize, returning same date 

        tz_name = tz_finder.timezone_at(lng=lon, lat=lat)
        if not tz_name:
            return metadata.capture_time  # cannot find timezone, returning same date

        tz = pytz.timezone(tz_name)
        
        return tz.localize(naive_dt)

    def _from_dms(self, val: str) -> float:
        """Convert exif lat/lon represented as degre/minute/second into decimal
        >>> _from_dms("1/1 55/1 123020/13567")
        1.9191854417991367
        >>> _from_dms("49/1 0/1 1885/76")
        49.00688961988304
        """
        deg_raw, min_raw, sec_raw = val.split(" ")
        deg_num, deg_dec = deg_raw.split("/")
        deg = float(deg_num) / float(deg_dec)
        min_num, min_dec = min_raw.split("/")
        min = float(min_num) / float(min_dec)
        sec_num, sec_dec = sec_raw.split("/")
        sec = float(sec_num) / float(sec_dec)

        return float(deg) + float(min) / 60 + float(sec) / 3600

    def _to_dms(self, value: float) -> Tuple[int, int, float]:
        """Return degree/minute/seconds for a decimal
        >>> _to_dms(38.889469)
        (38, 53, 22.0884)
        >>> _to_dms(43.7325)
        (43, 43, 57.0)
        >>> _to_dms(-43.7325)
        (43, 43, 57.0)
        """
        value = abs(value)
        deg = int(value)
        min = (value - deg) * 60
        sec = (min - int(min)) * 60

        return deg, int(min), round(sec, 8)

    def _to_exif_dms(self, value: float) -> str:
        """Return degree/minute/seconds string formated for the exif metadata for a decimal
        >>> _to_exif_dms(38.889469)
        '38/1 53/1 55221/2500'
        """
        from fractions import Fraction

        d, m, s = self._to_dms(value)
        f = Fraction.from_float(s).limit_denominator()  # limit fraction precision
        num_s, denomim_s = f.as_integer_ratio()
        return f"{d}/1 {m}/1 {num_s}/{denomim_s}"
