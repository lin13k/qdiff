from django.test import TestCase
from qdiff.utils.ciphers import FernetCipher


class FernetCipherTestCase(TestCase):

    def setUp(self):
        self.fc = FernetCipher(
            b'AkSkJRnLC0X_D0fw9EMcvxmeOz3opMZhponz536xbOs=')

    def testEncodeAndDecode(self):
        testText = 'this is a book'
        token = self.fc.encode(testText)
        decodedText = self.fc.decode(token)
        self.assertEqual(testText, decodedText)
