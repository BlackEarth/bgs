import logging, os, re, sys, subprocess
from glob import glob
from bmagick import Magick

log = logging.getLogger(__name__)


class GS:
    def __init__(self, gs=None, magick=None):
        """initialise the GS object.
        gs = the system 'gs' command
        """
        self.gs = gs or 'gs'
        self.magick = magick

    def __repr__(self):
        return "GS(%r)" % self.gs

    def render(
        self,
        srcfn,
        outfn=None,
        device='jpeg',
        res=600,
        alpha=4,
        quality=90,
        allpages=True,
        mogrify=None,
        magick=None,
    ):
        """use ghostscript to render output file(s) from the PDF
        srcfn = the absolute system path of the source file
        outfn = the absolute system path of the output file; if None, based on srcfn and device
        device = the device to use to create the output; implies the file extension
        res = the output resolution. Recommend 600 dpi or higher.
        alpha = the number of bits to use for the alpha value.
        quality = the jpeg quality: 100 = highest.
        allpages = whether to output all pages. If not True, only the first page.
        mogrify=None: if {...}, these are parameters to pass to Magick.mogrify()
        magick=None: the commandline command to use for mogrify, if any
        """
        # create the outfn from the srcfn by appending the output device extension.
        if outfn is None:
            outfn = os.path.splitext(srcfn)[0] + DEVICE_EXTENSIONS[device]
            if outfn == srcfn:
                outfn += DEVICE_EXTENSIONS[device]
        # normalize the output filename
        outfn = os.path.normpath(os.path.abspath(outfn))  # normalize path
        # make sure the output directory exists
        if not os.path.exists(os.path.dirname(outfn)):
            os.makedirs(os.path.dirname(outfn))

        if allpages is True and os.path.splitext(srcfn)[-1].lower() == '.pdf':
            # use ghostscript to count the pages in the PDF
            cmd = [
                self.gs,
                '-q',
                '-dNODISPLAY',
                '-c',
                "(%s) (r) file runpdfbegin pdfpagecount = quit" % srcfn,
            ]
            log.debug(cmd)
            out_pages = subprocess.check_output(cmd).decode('utf-8').strip()
            if out_pages == '':
                out_pages = '1'
            pages = int(out_pages)
            log.debug("%d page(s)" % pages)
        else:
            # assume one page
            pages = 1

        callargs = [
            self.gs,
            '-q',
            '-dSAFER',
            '-dBATCH',
            '-dNOPAUSE',
            '-dUseCropBox',
            '-sDEVICE=%s' % device,
            '-r%d' % res,
        ]
        if 'jpeg' in device:
            callargs += ['-dJPEGQ=%d' % quality]
        if 'png' in device or 'jpeg' in device or 'tiff' in device:
            callargs += ['-dTextAlphaBits=%d' % alpha, '-dGraphicsAlphaBits=%d' % alpha]

        if pages > 1:
            # add a counter to the output filename (outfn),
            # which tells gs to create a file for every page in the input
            # (without the counter, it just creates a single output file for the first page)
            fb, ext = os.path.splitext(outfn)
            n = len(re.split('.', str(pages))) - 1
            counter = "-%%0%dd" % n
            outfn = fb + counter + ext

            # remove any existing output filenames that match the pattern
            for existingfn in glob(fb + '*' + ext):
                os.remove(existingfn)
        else:
            callargs += ['-dFirstPage=1', '-dLastPage=1']

        callargs += ['-sOutputFile=%s' % outfn, srcfn]

        log.debug(callargs)
        subprocess.check_output(callargs, stderr=subprocess.STDOUT)

        output_filenames = sorted(glob(re.sub(r'%\d+d', '*', outfn)))
        
        if mogrify is not None:
            im = Magick(cmd=magick or self.magick)
            for filename in output_filenames:
                im.mogrify(filename, **mogrify)
        
        return output_filenames


DEVICE_EXTENSIONS = {
    'png16m': '.png',
    'png256': '.png',
    'png16': '.png',
    'pngmono': '.png',
    'pngmonod': '.png',
    'pngalpha': '.png',
    'pnggray': '.png',
    'jpeg': '.jpg',
    'jpeggray': '.jpg',
    'tiff48nc': '.tiff',  # rgb, 16bit per channel
    'tiff24nc': '.tiff',  # rgb, 8bit per channel
    'tiff12nc': '.tiff',  # rgb, 4bit per channel
    'tiffgray': '.tiff',  # grayscale, 8bit per channel
    'tiff64nc': '.tiff',  # cmyk, 16bit
    'tiff32nc': '.tiff',  # cmyk, 8bit
    'tiffsep': '.tiff',  # cmyk separation into 4 files + 1 composite
    'tiffsep1': '.tiff',
    'tiffscaled': '.tiff',
    'tiffscaled4': '.tiff',
    'tiffscaled8': '.tiff',
    'tiffscaled24': '.tiff',
    'tiffscaled32': '.tiff',
    'tiffcrle': '.tiff',
    'tiffg3': '.tiff',
    'tiffg32d': '.tiff',
    'tiffg4': '.tiff',
    'tifflzw': '.tiff',
    'tiffpack': '.tiff',
    'txtwrite': '.txt',
    'psdrgb': '.psd',
    'psdcmyk': '.psd',
    'pdfwrite': '.pdf',
}
