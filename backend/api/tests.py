# adicionei o type ignore apenas para não apresentar erros de interpretador
from django.contrib.auth.models import User # type: ignore
from rest_framework.test import APITestCase # type: ignore
from rest_framework import status # type: ignore
from .models import Asset, Category, Profile

class AssetTests(APITestCase):
    
    def setUp(self):
        
        # 1. Mock do Ator 'Administrador': 
        # Criamos um usuário e forçamos o perfil para simular o acesso privilegiado.
        self.admin_user = User.objects.create_user(username='admin', password='123')
        profile_admin, created = Profile.objects.get_or_create(user=self.admin_user)
        profile_admin.role = 'admin'
        profile_admin.save()
        self.admin_user.is_staff = True # Stub para permissão nativa do Django
        self.admin_user.save()
        self.admin_user.refresh_from_db()

        # 2. Mock do Ator 'Visualizador': 
        # Criamos um usuário com perfil restrito para testar o bloqueio (RN03).
        self.viewer_user = User.objects.create_user(username='viewer', password='123')
        profile_viewer, created = Profile.objects.get_or_create(user=self.viewer_user)
        profile_viewer.role = 'viewer'
        profile_viewer.save()
        self.viewer_user.refresh_from_db()

        # 3. Mock de Dependência (Entidade Relacionada):
        # O Ativo depende de uma Categoria existente, então criamos este stub.
        self.category = Category.objects.create(name='Eletrônicos', owner=self.admin_user)

        # Driver: Definição do endpoint (URL) que será testado
        self.url = '/api/assets/'

    # CT01: Teste de Caminho
    def test_create_asset_success(self):
        # RN01, RN02, RN03: Admin deve conseguir criar ativo válido
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "patrimonio": "PC-GAMER-01",
            "category": self.category.id,
            "field_values": []
        }
        # format='json' para garantir que a lista [] seja enviada corretamente
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Asset.objects.count(), 1)
        self.assertEqual(Asset.objects.get().patrimonio, 'PC-GAMER-01')
        self.assertEqual(Asset.objects.get().owner, self.admin_user)

    # CT02: Teste de Validação de Campo Obrigatório
    def test_create_asset_empty_patrimonio(self):
        # RN01: Não deve permitir patrimônio vazio.
        self.client.force_authenticate(user=self.admin_user)
        data = {
            "patrimonio": "", 
            "category": self.category.id,
            "field_values": []
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('patrimonio', response.data)

    # CT03: Teste de Exclusividade
    def test_create_asset_duplicate(self):
        # RN02: Não deve permitir patrimônio duplicado.
        self.client.force_authenticate(user=self.admin_user)
        
        # 1. Cria o primeiro (direto no banco, não precisa de field_values.....)
        Asset.objects.create(patrimonio="NOTE-01", category=self.category, owner=self.admin_user)
        
        # 2. Tenta criar o segundo igual via API
        data = {
            "patrimonio": "NOTE-01", 
            "category": self.category.id,
            "field_values": []
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('patrimonio', response.data)

    # CT04: Teste de Permissão
    def test_create_asset_permission_denied(self):
        # RN03: Usuário Viewer não pode criar ativos
        self.client.force_authenticate(user=self.viewer_user)
        data = {
            "patrimonio": "PC-INVADE",
            "category": self.category.id,
            "field_values": []
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)