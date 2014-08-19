# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'QuestionOptions.number_of_decimal'
        db.delete_column(u'bm_questionoptions', 'number_of_decimal')


    def backwards(self, orm):
        # Adding field 'QuestionOptions.number_of_decimal'
        db.add_column(u'bm_questionoptions', 'number_of_decimal',
                      self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=2),
                      keep_default=False)


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'bm.benchmark': {
            'Meta': {'object_name': 'Benchmark'},
            '_industry': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['social.LinkedInIndustry']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'db_column': "'industry_id'", 'blank': 'True'}),
            'approved': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'geographic_coverage': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'benchmarks'", 'symmetrical': 'False', 'to': u"orm['bm.Region']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'min_numbers_of_responses': ('django.db.models.fields.PositiveIntegerField', [], {'default': '5'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'overview': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'benchmarks'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'popular': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'bm.benchmarkinvitation': {
            'Meta': {'object_name': 'BenchmarkInvitation'},
            'benchmark': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invites'", 'to': u"orm['bm.Benchmark']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed_to_forward_invite': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'invites'", 'to': u"orm['social.Contact']"}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'sent_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '45'})
        },
        u'bm.benchmarklink': {
            'Meta': {'object_name': 'BenchmarkLink'},
            'benchmark': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'links'", 'to': u"orm['bm.Benchmark']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '36'})
        },
        u'bm.benchmarkrating': {
            'Meta': {'object_name': 'BenchmarkRating'},
            'benchmark': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ratings'", 'to': u"orm['bm.Benchmark']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rating': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'})
        },
        u'bm.numericstatistic': {
            'Meta': {'object_name': 'NumericStatistic'},
            'avg': ('django.db.models.fields.FloatField', [], {}),
            'benchmark': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'numeric_statistic'", 'to': u"orm['bm.Benchmark']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max': ('django.db.models.fields.FloatField', [], {}),
            'min': ('django.db.models.fields.FloatField', [], {}),
            'sd': ('django.db.models.fields.FloatField', [], {})
        },
        u'bm.question': {
            'Meta': {'object_name': 'Question'},
            'benchmark': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'question'", 'to': u"orm['bm.Benchmark']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        u'bm.questionchoice': {
            'Meta': {'object_name': 'QuestionChoice'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'choices'", 'to': u"orm['bm.Question']"})
        },
        u'bm.questionoptions': {
            'Meta': {'object_name': 'QuestionOptions'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'options'", 'to': u"orm['bm.Question']"}),
            'units': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'bm.questionranking': {
            'Meta': {'object_name': 'QuestionRanking'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ranks'", 'to': u"orm['bm.Question']"})
        },
        u'bm.questionresponse': {
            'Meta': {'object_name': 'QuestionResponse'},
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'responses'", 'to': u"orm['bm.Question']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'responses'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"})
        },
        u'bm.region': {
            'Meta': {'object_name': 'Region'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bm.Region']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'regions'", 'to': u"orm['bm.RegionType']"})
        },
        u'bm.regiontype': {
            'Meta': {'object_name': 'RegionType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '45'})
        },
        u'bm.responsechoice': {
            'Meta': {'object_name': 'ResponseChoice'},
            'choice': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bm.QuestionChoice']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'data_choices'", 'to': u"orm['bm.QuestionResponse']"})
        },
        u'bm.responsenumeric': {
            'Meta': {'object_name': 'ResponseNumeric'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'data_numeric'", 'to': u"orm['bm.QuestionResponse']"}),
            'value': ('django.db.models.fields.IntegerField', [], {})
        },
        u'bm.responserange': {
            'Meta': {'object_name': 'ResponseRange'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max': ('django.db.models.fields.IntegerField', [], {}),
            'min': ('django.db.models.fields.IntegerField', [], {}),
            'response': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'data_range'", 'to': u"orm['bm.QuestionResponse']"})
        },
        u'bm.responseranking': {
            'Meta': {'object_name': 'ResponseRanking'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rank': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bm.QuestionRanking']"}),
            'response': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'data_ranks'", 'to': u"orm['bm.QuestionResponse']"}),
            'value': ('django.db.models.fields.IntegerField', [], {})
        },
        u'bm.seriesstatistic': {
            'Meta': {'object_name': 'SeriesStatistic'},
            'benchmark': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'series_statistic'", 'to': u"orm['bm.Benchmark']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'series': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sub_series': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'social.company': {
            'Meta': {'object_name': 'Company'},
            '_industry': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'companies'", 'db_column': "'industry_id'", 'on_delete': 'models.SET_NULL', 'to': u"orm['social.LinkedInIndustry']", 'blank': 'True', 'null': 'True'}),
            'code': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        u'social.contact': {
            'Meta': {'unique_together': "(('code', 'provider'),)", 'object_name': 'Contact'},
            '_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'db_column': "'email'", 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'company': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'employees'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['social.Company']"}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'headline': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'contacts'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['bm.Region']"}),
            'owners': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'contacts'", 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'provider': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        u'social.linkedinindustry': {
            'Meta': {'object_name': 'LinkedInIndustry'},
            'code': ('django.db.models.fields.PositiveSmallIntegerField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['bm']