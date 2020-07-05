#pip install allennlp
#pip install word2number
#pip install fuzzywuzzy

from allennlp.predictors import Predictor
from word2number import w2n
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

al = Predictor.from_path("https://s3-us-west-2.amazonaws.com/allennlp/models/fine-grained-ner-model-elmo-2018.12.21.tar.gz")


#FUNCTION TO EXTRACT NAME AND AGE USING ALLENNLP LIBRARY OF NAME ENTITY RECOGNITION
def find_name_age(list_of_entity):

	#print(list_of_entity)
	total_entry = len(list_of_entity)

	f_name = ""
	m_name = ""
	l_name = ""

	full_name = []
	age = []
	location = set()

	for i in range(total_entry):

#-------------------------------------FOR PERSON NAME-----------------------------------------

		if(list_of_entity[i]['type'] == "B-PERSON"):

			f_name = list_of_entity[i]['entity']

			if(list_of_entity[i+1]['type'] == "I-PERSON" and (i+1)!=total_entry):

				m_name = list_of_entity[i+1]['entity']

				if(list_of_entity[i+2]['type'] == "L-PERSON" and (i+2)!=total_entry):
					l_name = list_of_entity[i+2]['entity']

			elif(list_of_entity[i+1]['type'] == "L-PERSON" and (i+1)!=total_entry):
				l_name = list_of_entity[i+1]['entity']

			else:
				m_name = ""
				l_name = ""
			
			if not m_name:
				fname = f_name + " " + l_name
			else:
				fname = f_name + " " + m_name + " " + l_name

			f_name = ""
			m_name = ""
			l_name = ""
			full_name.append(fname.lower())			
		
		elif(list_of_entity[i]['type'] == "U-PERSON"):

			f_name = list_of_entity[i]['entity']
			m_name = ""
			l_name = ""

			full_name.append(f_name.lower())

			f_name = ""
			m_name = ""
			l_name = ""	

#-------------------------------FOR LOCATION EXTRACTION------------------------------------			

		elif(list_of_entity[i]['type'] == "U-GPE"):
			location.add(list_of_entity[i]['entity'].lower())	

#-------------------------------FOR AGE EXTRACTION------------------------------------------

		else:

			if(list_of_entity[i]['type'] != "I-PERSON" and list_of_entity[i]['type'] != "L-PERSON"):


				if((list_of_entity[i]['type'] == "B-DATE" or list_of_entity[i]['type'] == "I-DATE" or list_of_entity[i]['type'] == "L-DATE") and list_of_entity[i]['entity'].isnumeric()):
					age.append(int(list_of_entity[i]['entity']))

				elif(list_of_entity[i]['type'] == "B-DATE" and (list_of_entity[i+1]['type'] == "I-DATE" or list_of_entity[i+1]['type'] == "L-DATE") and (i+1)!=total_entry and (list_of_entity[i+1]['type'] != '-' or list_of_entity[i+1]['type'] != '/') and list_of_entity[i]['entity'].isnumeric()):
					idate = ""
					ldate = ""
					bdate = list_of_entity[i]['entity']
					word_age = ""
					if list_of_entity[i+1]['type'] == "I-DATE":
						idate = check_num(list_of_entity[i+1]['entity'])
						if idate:
							i_date = list_of_entity[i+1]['entity']
						else:
							i_date = ""

						word_age = i_date

					if list_of_entity[i+1]['type'] == "L-DATE":
						
						ldate = check_num(list_of_entity[i+1]['entity'])
						
						if ldate:
							l_date = list_of_entity[i+1]['entity']
						else:
							l_date = ""

						word_age = l_date

					new_age = bdate+" "+word_age
					
					age.append(int(w2n.word_to_num(new_age)))

	return full_name,age,location


#FUNCTION TO CHECK IF WORD IS NUMERIC e.g 'one' is numeric but 'years' is not numeric 
def check_num(word):

	try:
		x = w2n.word_to_num(word)
		return True
	except:
		return False

			
#FUNCTION TO EXTRACT NAME,AGE FROM NEWS AND RETURNS LIST OF NAME AND LIST OF AGE
def extract_entity(news):
	results = al.predict(news)

	list_of_entity = []
	for word,tag in zip(results["words"], results["tags"]):
		dic = {}
		dic["entity"] = word
		dic["type"] = tag
		list_of_entity.append(dic)

	name_of_person , age , location = find_name_age(list_of_entity)

	return name_of_person,age,location

#FUNCTION TO CALCULATE SCORE USING FUZZYWUZZY
def final_score(news_name,news_age,news_location,form_name,form_age,form_location):

	name_score = 0
	age_score = 0
	location_score = 0

	age_range = {0:1 , 1:0.8 , 2:0.6 , 3:0.5 , 4:0.4 , 5:0.2}

#-----------------------------NAME SCORE----------------------------------------

	name = ""

	for each_name in news_name:
		x = fuzz.token_sort_ratio(each_name,form_name.lower())
		if x > name_score:
			name_score = x
			name = each_name
		
		else:
			continue
	
#-----------------------------AGE SCORE-----------------------------------------

	for each_age in news_age:

		diff = abs(each_age-form_age)
		if diff >=0 and diff<=5:
			age_score = max(age_score , age_range[diff])

#-----------------------------LOCATION SCORE------------------------------------

	for each_loc in news_location:
		location_score = max(location_score,fuzz.token_sort_ratio(news_location,form_location.lower()))

	total_score = 0.8*name_score + 0.15*location_score + 0.05*age_score*100

	return total_score , name

#FUNCTION TO CALCULATE THE FINAL SCORE 
def get_score(news): #pass other parameters like form_name,form_location,form_age

	#list of news
	#for each_news in news:
	#	name = ""

	news_name = []
	news_age = []
	news_location = []
	form_name = "rami abdel"
	form_age = 23
	form_location = "iraq"
	
	news_name , news_age , news_location = extract_entity(news)
	#print(news_name)
	#print(news_age)
	#print(news_location)

	score , name_in_news = final_score(news_name,news_age,news_location,form_name,form_age,form_location) #form_name,form_age,form_location

	print(score,name_in_news)

def main():
	#Nothing here

	#get each news one by one from the elasticDB

	news = """At least 11 Assad regime and allied fighters were killed Thursday in an attack carried out by Daesh terrorist group in Syria's Deir el-Zour, a monitoring group said.

The fighters died in an attack on their vehicle between al-Sokhna and al-Shula in the area straddling Homs and Deir el-Zour provinces, the Syrian Observatory for Human Rights said.

Rami Abdel Rahman, the head of the U.K.-based monitoring organization, could not immediately provide further details but warned that the casualty toll could rise.

There was no immediate claim from Daesh terrorists, who lost all territory last year but has continued to conduct frequent guerrilla-style attacks in eastern Syria.

At least 27 regime and allied fighters were killed in an attack by the terrorist group in the same desert area a month ago.

Daesh has also carried out deadly attacks in Iraq in recent weeks.

Observers have warned that border closures and mobilization of security resources due to the coronavirus pandemic could give rise to a surge in Daesh attacks.

The terrorist group, which once administered a proto-state the size of Great Britain, no longer has fixed positions, but it still has hundreds of fighters hunkered down in desert hideouts.
	"""
	get_score(news)

if __name__ == '__main__':
	main()