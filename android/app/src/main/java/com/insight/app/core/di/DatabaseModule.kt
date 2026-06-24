package com.insight.app.core.di

import android.content.Context
import androidx.room.Room
import com.insight.app.core.data.local.InsightDatabase
import com.insight.app.core.data.local.dao.InsightDao
import com.insight.app.core.data.local.dao.TopicDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): InsightDatabase {
        return Room.databaseBuilder(
            context,
            InsightDatabase::class.java,
            "insight.db",
        ).build()
    }

    @Provides
    fun provideInsightDao(db: InsightDatabase): InsightDao = db.insightDao()

    @Provides
    fun provideTopicDao(db: InsightDatabase): TopicDao = db.topicDao()
}
