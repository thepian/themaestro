from django import test
from django.core import mail
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from models import ActivationRecord

class RegistrationTestCase(test.TestCase):

    def setUp(self):
        self.name = 'megatest'
        self.email = 'something@example.com'
        self.user = ActivationRecord.registrations.create_inactive_user(name=self.name, email=self.email, password=self.name)
        self.em = mail.outbox[0]
        self.ar = self.user.activationrecord_set.get(type='A')

    def testUserCreate(self):
        self.assertEquals(self.user.is_active, False)

    def testMailExist(self):
        self.assertEqual(len(mail.outbox), 1)

    def testSubjectValid(self):
        self.assertEqual(self.em.subject, 'Activate your new account at example.com')

    def testContentValid(self):
        self.assertNotEqual(self.em.body.find(self.ar.activation_key), -1)

    def testActivation(self):
        user_act = ActivationRecord.registrations.activate_user(self.ar.activation_key)
        self.assertEqual(self.user, user_act)


class EmailChangeTestCase(test.TestCase):

    def setUp(self):
        self.name = 'test'
        self.old_email = 'something@example.com'
        self.new_email = 'other@example.com'
        self.user = User.objects.create_user(self.name, self.old_email, self.name)

    def testEmailChange(self):
        self.assertEquals(self.client.login(email=self.old_email, password=self.name), True)
        response = self.client.post(reverse('profile_edit'), {'email': self.new_email})
        self.assertEqual(len(mail.outbox), 1)
