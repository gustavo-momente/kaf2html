import KafNafParserPy as kafp
import codecs
import markup
import cgi
import argparse
import os

def create_parsers():
	#parser for the main program
	parser = argparse.ArgumentParser(description='A simple script to better visualize named entities in a kaf file')
	parser.add_argument('-f', '-file', metavar='<in_file.kaf>', required=False, help='Source file (won\'t be taken into account when using -dir option)')
	parser.add_argument('-o', '-out', metavar='<out>', default=None, help='Output file name, won\'t be taken into account when using -dir option (default to : in_file.html)')
	parser.add_argument('-d', '-dir', metavar='<dir>', required=False, help='Bulk process all files in this directory')
	parser.add_argument('-css', metavar='<style.css>', required=False, default='style.css', help='name of the css style sheet to be used')
	parser.add_argument('-l', '-lang', metavar='<language>', default='fr', help='html language tag')
	return parser


def get_entities_dic(kaf):
	found_entities = dict()
	entities_set = set()
	for entity in kaf.get_entities():
		_type = entity.get_type().title()
		entities_set.add(_type)
		for ref in entity.get_references():
			span = ref.get_span().get_span_ids()
			for i in xrange(len(span)):
				found_entities[span[i].replace("t", "w", 1)] = {"start" : i == 0, "end": i == len(span) -1}
				if found_entities[span[i].replace("t", "w", 1)]['start']:
					found_entities[span[i].replace("t", "w", 1)]['type'] = _type
	return found_entities, entities_set

def gen_html(kaf_file, out, title="Simple kaf2html", css="style.css", lang="fr"):
	# Read the kaf file
	kaf = kafp.KafNafParser(kaf_file)

	# First, we see witch entities were found
	found_entities, entities_set = get_entities_dic(kaf)

	# Then we create an empty html page
	page = markup.page()
	page.init(title=title, css=css, charset="UTF-8", lang=lang)

	# Now we can generate the body's elements and text
	para = 1
	end = None
	this_para = int()
	words = []
	for token in kaf.get_tokens():
		# We have to check for new paragraphs, so that them are properly
		# displayed in the output
		this_para = int(token.get_node().get('para')) 
		if para != this_para:
			for i in xrange(this_para - para):
				words.append("\n")
				words.append("<br>")
				end += 2
			para = this_para
		
		# And we have to take into account spaces, by counting the offsets
		# between each token
		try:
			for i in xrange(int(token.get_offset()) - end):
				words.append(" ")
		except TypeError:
			pass
		end = int(token.get_offset()) + int(token.get_length())
		
		# We get the current token id and we check if it is an entity
		tid = token.get_id() 
		is_entity = tid in found_entities

		# As there can be multi-word entities we have to take that into account
		# For that we check if this is the starting token, if it's we open
		# the html element
		if is_entity:
			if found_entities[tid]['start']:
				words.append("<span title=\"{}\" class=\"label {}\">".format(found_entities[tid]['type'], found_entities[tid]['type']))

		# Adding the proper text and taking into account html special characters
		words.append(cgi.escape(token.get_text()))

		# Finally, it's the last word of an entity we close the span
		if is_entity:
			if found_entities[tid]['end']:
				words.append("</span>")
	
	page.div(class_="center")
	page.p('NER Legend: ', class_="title")
	for t in sorted(entities_set):
		page.span(t, class_="label {}".format(t))
	page.div.close()

	# Finally, we put the text and the elements inside a div and we save it
	# to a file
	page.p('Text: ', class_="title center")
	page.div("".join(words), class_="center main_text")
	with codecs.open(out, 'w', "utf-8") as f:
		f.write(page.__str__())
	del words


def gen_out_name(path):
	return (os.path.splitext(path)[0] + '.html')


def main():
	parser = create_parsers()
	args = vars(parser.parse_args())
	css = args['css']
	lang = args['l']
	dir_ = args['d']
	in_file = args['f']
	out_file = args['o']

	to_process = list()

	if in_file is not None:
		if out_file is not None:
			to_process.append((in_file, out_file))
		else:
			to_process.append((in_file, gen_out_name(in_file)))

	if dir_ is not None:
		for root, dirs, files in os.walk(dir_):
			for file in files:
				if file.endswith(".kaf"):
					f = os.path.join(root, file)
					to_process.append((f, gen_out_name(f)))

	for process in to_process:
		gen_html(process[0], process[1], title=os.path.splitext(os.path.basename(process[0]))[0], css=css, lang=lang)
		print process[0]

	if len(to_process) == 0:
		parser.print_help()

if __name__ == '__main__':
	main()