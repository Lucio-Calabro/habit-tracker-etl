CREATE TABLE raw_events (
	raw_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
	received_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	data_source VARCHAR(50),
	message_id VARCHAR(100) UNIQUE,                        
    run_id VARCHAR(255),                            
	payload JSONB
);

CREATE TABLE habits (
	habit_id SERIAL PRIMARY KEY,
	name VARCHAR(50) UNIQUE,
	unit VARCHAR(50),
	monthly_target INT,
	is_active BOOL DEFAULT TRUE
);

CREATE TABLE habits_logs(
	date DATE,
	value NUMERIC(5,2),
	habit_id INT,
	PRIMARY KEY (date,habit_id),
	FOREIGN KEY (habit_id) REFERENCES habits(habit_id)
	
);

CREATE TABLE monthly_progress (
	month_date VARCHAR(6),
	habit_id INT,
	mtd_value NUMERIC,
	last_updated_at TIMESTAMP,
	
	PRIMARY KEY (month_date,habit_id),
	
	FOREIGN KEY (habit_id) REFERENCES habits (habit_id)
);

CREATE TABLE monthly_report (
	month_date VARCHAR(6),
	habit_id INT,
	final_value NUMERIC,
	target_value NUMERIC,
	compliance_ratio NUMERIC(5,2),
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	
	PRIMARY KEY (month_date,habit_id),
	
	FOREIGN KEY (habit_id) REFERENCES habits (habit_id)
);
    