from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username='auth')
        super().setUpClass()
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
        )
        cls.group = Group.objects.create(
            title='Test_title',
            description='Test_description',
            slug='Group',
        )

    def test_PostModelTest(self):
        """ Проверям корректность работы метода __str__"""
        post = PostsModelTest.post
        post_text = post.text[:15]
        self.assertEqual(post_text[:15], str(post))
        group = PostsModelTest.group
        self.assertEqual(group.title, str(group))

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostsModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected
                )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostsModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, expected in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected
                )
