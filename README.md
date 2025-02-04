# Laptop Research & Analysis Platform

A comprehensive platform to crawl, analyze, and recommend laptops based on user preferences.

## Project Structure

The platform consists of four interconnected applications:

### 1. [Laptop Dashboard](https://github.com/SlayerK15/laptop_analyzer) 
- Frontend web application for visualizing laptop data
- Interactive user interface for comparing specifications 
- Built with React and Node.js
- Status: 🚧 Work in Progress

### 2. [Laptop Analyzer](https://github.com/SlayerK15/laptop_analyzer)
- Data cleaning and preprocessing engine
- Standardizes and validates crawled data
- Prepares clean dataset for dashboard and recommender(currently manaul)
- Status: ✅ Complete

### 3. [Laptop Crawler](https://github.com/SlayerK15/Laptop_Crawler)
- Web scraping tool for collecting laptop data
- Extracts specifications from online retailers
- Built with Python
- Status: ✅ Complete

### 4. Laptop Recommender
- AI-powered recommendation system 
- Suggests laptops based on user requirements
- Uses cleaned data from analyzer
- Status: 🚧 In Development

## Data Pipeline

1. **Crawler** → Scrapes raw laptop data from websites
2. **Analyzer** → Cleans and standardizes the raw data
3. **Dashboard** → Visualizes the clean data
4. **Recommender** → Uses clean data for personalized suggestions

## Current Focus

- Building interactive dashboard interface
- Developing recommendation algorithms
- Ongoing data cleaning and validation
- Integration of components

## Features

### Dashboard (In Progress)
- Interactive data visualization
- Specification comparison
- Price tracking
- Performance metrics

### Analyzer (Complete)
- Data cleaning
- Format standardization  
- Missing value handling
- Duplicate removal
- Data validation

### Crawler (Complete)
- Automated web scraping
- Multiple source support
- Regular data updates
- Specification extraction

### Recommender (In Development)
- Personalized suggestions
- Price-performance optimization
- Usage-based recommendations
- Budget considerations

## Data Structure

The standardized data includes:
- URL
- Title 
- Price
- Brand
- RAM
- CPU Brand & Model
- GPU Brand & Model
- Display Size
- Refresh Rate
- Resolution
- Storage

## Development Status

- Analyzer: ✅ Complete
- Crawler: ✅ Complete 
- Dashboard: 🚧 In Development
- Recommender: 🚧 In Development

## Links

- [Frontend Dashboard](Coming Soon)
- [Data Analyzer](https://github.com/SlayerK15/laptop_analyzer)
- [Web Crawler](https://github.com/SlayerK15/Laptop_Crawler)
- Recommender System (Coming Soon)

## Next Steps

1. Complete dashboard UI development
2. Implement recommendation algorithms
3. Integration testing
4. User testing and feedback
5. Performance optimization
