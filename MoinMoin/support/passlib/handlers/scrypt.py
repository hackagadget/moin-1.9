"""passlib.handlers.scrypt -- scrypt password hash"""
#=============================================================================
# imports
#=============================================================================

# core
import logging; log = logging.getLogger(__name__)
# site
# pkg
from passlib.crypto import scrypt as _scrypt
from passlib.utils import h64, to_bytes
from passlib.utils.binary import h64, b64s_decode, b64s_encode
from passlib.utils.compat import u, bascii_to_str, suppress_cause
from passlib.utils.decor import classproperty
import passlib.utils.handlers as uh
# local
__all__ = [
    "scrypt",
]

#=============================================================================
# scrypt format identifiers
#=============================================================================

IDENT_SCRYPT = u("$scrypt$")  # identifier used by passlib
IDENT_7 = u("$7$")  # used by official scrypt spec

_UDOLLAR = u("$")

#=============================================================================
# handler
#=============================================================================
class scrypt(uh.ParallelismMixin, uh.HasRounds, uh.HasRawSalt, uh.HasRawChecksum, uh.HasManyIdents,
             uh.GenericHandler):
    """This class implements an SCrypt-based password [#scrypt-home]_ hash, and follows the :ref:`password-hash-api`.

    It supports a variable-length salt, a variable number of rounds,
    as well as some custom tuning parameters unique to scrypt (see below).

    The :meth:`~passlib.ifc.PasswordHash.using` method accepts the following optional keywords:

    :type salt: str
    :param salt:
        Optional salt string.
        If specified, the length must be between 0-1024 bytes.
        If not specified, one will be auto-generated (this is recommended).

    :type salt_size: int
    :param salt_size:
        Optional number of bytes to use when autogenerating new salts.
        Defaults to 16 bytes, but can be any value between 0 and 1024.

    :type rounds: int
    :param rounds:
        Optional number of rounds to use.
        Defaults to 16, but must be within ``range(1,32)``.

        .. warning::

            Unlike many hash algorithms, increasing the rounds value
            will increase both the time *and memory* required to hash a password.

    :type block_size: int
    :param block_size:
        Optional block size to pass to scrypt hash function (the ``r`` parameter).
        Useful for tuning scrypt to optimal performance for your CPU architecture.
        Defaults to 8.

    :type parallelism: int
    :param parallelism:
        Optional parallelism to pass to scrypt hash function (the ``p`` parameter).
        Defaults to 1.

    :type relaxed: bool
    :param relaxed:
        By default, providing an invalid value for one of the other
        keywords will result in a :exc:`ValueError`. If ``relaxed=True``,
        and the error can be corrected, a :exc:`~passlib.exc.PasslibHashWarning`
        will be issued instead. Correctable errors include ``rounds``
        that are too small or too large, and ``salt`` strings that are too long.

    .. note::

        The underlying scrypt hash function has a number of limitations
        on it's parameter values, which forbids certain combinations of settings.
        The requirements are:

        * ``linear_rounds = 2**<some positive integer>``
        * ``linear_rounds < 2**(16 * block_size)``
        * ``block_size * parallelism <= 2**30-1``

    .. todo::

        This class currently does not support configuring default values
        for ``block_size`` or ``parallelism`` via a :class:`~passlib.context.CryptContext`
        configuration.
    """

    #===================================================================
    # class attrs
    #===================================================================

    #------------------------
    # PasswordHash
    #------------------------
    name = "scrypt"
    setting_kwds = ("ident", "salt", "salt_size", "rounds", "block_size", "parallelism")

    #------------------------
    # GenericHandler
    #------------------------
    # NOTE: scrypt supports arbitrary output sizes. since it's output runs through
    #       pbkdf2-hmac-sha256 before returning, and this could be raised eventually...
    #       but a 256-bit digest is more than sufficient for password hashing.
    # XXX: make checksum size configurable? could merge w/ argon2 code that does this.
    checksum_size = 32

    #------------------------
    # HasManyIdents
    #------------------------
    default_ident = IDENT_SCRYPT
    ident_values = (IDENT_SCRYPT, IDENT_7)

    #------------------------
    # HasRawSalt
    #------------------------
    default_salt_size = 16
    max_salt_size = 1024

    #------------------------
    # HasRounds
    #------------------------
    # TODO: would like to dynamically pick this based on system
    default_rounds = 16
    min_rounds = 1
    max_rounds = 31  # limited by scrypt alg
    rounds_cost = "log2"

    # TODO: make default block size configurable via using(), and deprecatable via .needs_update()

    #===================================================================
    # instance attrs
    #===================================================================

    #: default parallelism setting (min=1 currently hardcoded in mixin)
    parallelism = 1

    #: default block size setting
    block_size = 8

    #===================================================================
    # variant constructor
    #===================================================================

    @classmethod
    def using(cls, block_size=None, **kwds):
        subcls = super(scrypt, cls).using(**kwds)
        if block_size is not None:
            if isinstance(block_size, uh.native_string_types):
                block_size = int(block_size)
            subcls.block_size = subcls._norm_block_size(block_size, relaxed=kwds.get("relaxed"))

        # make sure param combination is valid for scrypt()
        try:
            _scrypt.validate(1 << cls.default_rounds, cls.block_size, cls.parallelism)
        except ValueError as err:
            raise suppress_cause(ValueError("scrypt: invalid settings combination: " + str(err)))

        return subcls

    #===================================================================
    # parsing
    #===================================================================

    @classmethod
    def from_string(cls, hash):
        return cls(**cls.parse(hash))

    @classmethod
    def parse(cls, hash):
        ident, suffix = cls._parse_ident(hash)
        func = getattr(cls, "_parse_%s_string" % ident.strip(_UDOLLAR), None)
        if func:
            return func(suffix)
        else:
            raise uh.exc.InvalidHashError(cls)

    #
    # passlib's format:
    #   $scrypt$ln=<logN>,r=<r>,p=<p>$<salt>[$<digest>]
    # where:
    #   logN, r, p -- decimal-encoded positive integer, no zero-padding
    #   logN -- log cost setting
    #   r -- block size setting (usually 8)
    #   p -- parallelism setting (usually 1)
    #   salt, digest -- b64-nopad encoded bytes
    #

    @classmethod
    def _parse_scrypt_string(cls, suffix):
        # break params, salt, and digest sections
        parts = suffix.split("$")
        if len(parts) == 3:
            params, salt, digest = parts
        elif len(parts) == 2:
            params, salt = parts
            digest = None
        else:
            raise uh.exc.MalformedHashError(cls, "malformed hash")

        # break params apart
        parts = params.split(",")
        if len(parts) == 3:
            nstr, bstr, pstr = parts
            assert nstr.startswith("ln=")
            assert bstr.startswith("r=")
            assert pstr.startswith("p=")
        else:
            raise uh.exc.MalformedHashError(cls, "malformed settings field")

        return dict(
            ident=IDENT_SCRYPT,
            rounds=int(nstr[3:]),
            block_size=int(bstr[2:]),
            parallelism=int(pstr[2:]),
            salt=b64s_decode(salt.encode("ascii")),
            checksum=b64s_decode(digest.encode("ascii")) if digest else None,
            )

    #
    # official format specification defined at
    #   https://gitlab.com/jas/scrypt-unix-crypt/blob/master/unix-scrypt.txt
    # format:
    #   $7$<N><rrrrr><ppppp><salt...>[$<digest>]
    #       0  12345  67890  1
    # where:
    #   All bytes use h64-little-endian encoding
    #   N: 6-bit log cost setting
    #   r: 30-bit block size setting
    #   p: 30-bit parallelism setting
    #   salt: variable length salt bytes
    #   digest: fixed 32-byte digest
    #

    @classmethod
    def _parse_7_string(cls, suffix):
        # XXX: annoyingly, official spec embeds salt *raw*, yet doesn't specify a hash encoding.
        #      so assuming only h64 chars are valid for salt, and are ASCII encoded.

        # split into params & digest
        parts = suffix.encode("ascii").split(b"$")
        if len(parts) == 2:
            params, digest = parts
        elif len(parts) == 1:
            params, = parts
            digest = None
        else:
            raise uh.exc.MalformedHashError()

        # parse params & return
        if len(params) < 11:
            raise uh.exc.MalformedHashError(cls, "params field too short")
        return dict(
            ident=IDENT_7,
            rounds=h64.decode_int6(params[:1]),
            block_size=h64.decode_int30(params[1:6]),
            parallelism=h64.decode_int30(params[6:11]),
            salt=params[11:],
            checksum=h64.decode_bytes(digest) if digest else None,
        )

    #===================================================================
    # formatting
    #===================================================================
    def to_string(self):
        ident = self.ident
        if ident == IDENT_SCRYPT:
            return "$scrypt$ln=%d,r=%d,p=%d$%s$%s" % (
                self.rounds,
                self.block_size,
                self.parallelism,
                bascii_to_str(b64s_encode(self.salt)),
                bascii_to_str(b64s_encode(self.checksum)),
            )
        else:
            assert ident == IDENT_7
            salt = self.salt
            try:
                salt.decode("ascii")
            except UnicodeDecodeError:
                raise suppress_cause(NotImplementedError("scrypt $7$ hashes dont support non-ascii salts"))
            return bascii_to_str(b"".join([
                b"$7$",
                h64.encode_int6(self.rounds),
                h64.encode_int30(self.block_size),
                h64.encode_int30(self.parallelism),
                self.salt,
                b"$",
                h64.encode_bytes(self.checksum)
            ]))

    #===================================================================
    # init
    #===================================================================
    def __init__(self, block_size=None, **kwds):
        super(scrypt, self).__init__(**kwds)

        # init block size
        if block_size is None:
            assert uh.validate_default_value(self, self.block_size, self._norm_block_size,
                                             param="block_size")
        else:
            self.block_size = self._norm_block_size(block_size)

        # NOTE: if hash contains invalid complex constraint, relying on error
        #       being raised by scrypt call in _calc_checksum()

    @classmethod
    def _norm_block_size(cls, block_size, relaxed=False):
        return uh.norm_integer(cls, block_size, min=1, param="block_size", relaxed=relaxed)

    def _generate_salt(self):
        salt = super(scrypt, self)._generate_salt()
        if self.ident == IDENT_7:
            # this format doesn't support non-ascii salts.
            # as workaround, we take raw bytes, encoded to base64
            salt = b64s_encode(salt)
        return salt

    #===================================================================
    # backend configuration
    # NOTE: this following HasManyBackends' API, but provides it's own implementation,
    #       which actually switches the backend that 'passlib.crypto.scrypt.scrypt()' uses.
    #===================================================================

    @classproperty
    def backends(cls):
        return _scrypt.backend_values

    @classmethod
    def get_backend(cls):
        return _scrypt.backend

    @classmethod
    def has_backend(cls, name="any"):
        try:
            cls.set_backend(name, dryrun=True)
            return True
        except uh.exc.MissingBackendError:
            return False

    @classmethod
    def set_backend(cls, name="any", dryrun=False):
        _scrypt._set_backend(name, dryrun=dryrun)

    #===================================================================
    # digest calculation
    #===================================================================
    def _calc_checksum(self, secret):
        secret = to_bytes(secret, param="secret")
        return _scrypt.scrypt(secret, self.salt, n=(1 << self.rounds), r=self.block_size,
                              p=self.parallelism, keylen=self.checksum_size)

    #===================================================================
    # hash migration
    #===================================================================

    def _calc_needs_update(self, **kwds):
        """
        mark hash as needing update if rounds is outside desired bounds.
        """
        # XXX: for now, marking all hashes which don't have matching block_size setting
        if self.block_size != type(self).block_size:
            return True
        return super(scrypt, self)._calc_needs_update(**kwds)

    #===================================================================
    # eoc
    #===================================================================

#=============================================================================
# eof
#=============================================================================
